"""
recording_service.py — Handles call recording assembly and transcript persistence
for the AI Dialer.
"""
import os
import json
import base64
import asyncio
import time
import logging
import httpx

from database import save_call_transcript


async def save_call_recording_and_transcript(
    stream_sid,
    _call_lead_id,
    _exotel_call_sid,
    chat_history,
    _recording_mic_chunks,
    _tts_recording_buffers,
    _call_start_time,
    EXOTEL_API_KEY,
    EXOTEL_API_TOKEN,
    EXOTEL_ACCOUNT_SID,
    _campaign_id=None,
):
    """
    Save the call transcript to the DB, fetch the Exotel recording (with retries),
    and fall back to server-side stereo WAV merge when Exotel recording is unavailable.
    """
    ws_logger = logging.getLogger("uvicorn.error")

    transcript_turns = []
    for msg in chat_history:
        role = "AI" if msg.get("role") == "model" else "User"
        text = ""
        parts = msg.get("parts", [])
        if parts and isinstance(parts[0], dict):
            text = parts[0].get("text", "")
        elif parts and isinstance(parts[0], str):
            text = parts[0]
        if text:
            transcript_turns.append({"role": role, "text": text})

    recording_url = None

    # --- Exotel recording fetch with retries ---
    if _exotel_call_sid:
        try:
            ws_logger.info(f"[RECORDING] Fetching for SID: {_exotel_call_sid}")
            creds = f"{EXOTEL_API_KEY}:{EXOTEL_API_TOKEN}"
            auth_b64 = base64.b64encode(creds.encode()).decode()
            rec_api_url = f"https://api.exotel.com/v1/Accounts/{EXOTEL_ACCOUNT_SID}/Calls/{_exotel_call_sid}/Recording.json"

            rec_resp = None
            for _attempt in range(6):
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as _hc:
                    rec_resp = await _hc.get(rec_api_url, headers={"Authorization": f"Basic {auth_b64}"})

                if rec_resp.status_code != 200:
                    ws_logger.warning(f"[RECORDING] Exotel returned {rec_resp.status_code}, attempt {_attempt+1}")
                    await asyncio.sleep(10)
                    continue

                content_type = rec_resp.headers.get("content-type", "")

                # Check if direct audio bytes
                if "audio" in content_type and len(rec_resp.content) > 1000:
                    _rec_dir = os.path.join(os.path.dirname(__file__), "recordings")
                    os.makedirs(_rec_dir, exist_ok=True)
                    ext = "wav" if "wav" in content_type else ("ogg" if "ogg" in content_type else "mp3")
                    _rec_fname = f"call_{_call_lead_id}_{int(_call_start_time)}.{ext}"
                    _rec_path = os.path.join(_rec_dir, _rec_fname)
                    with open(_rec_path, "wb") as f:
                        f.write(rec_resp.content)
                    recording_url = f"/api/recordings/{_rec_fname}"
                    ws_logger.info(f"[RECORDING] Saved direct audio: {_rec_path} ({len(rec_resp.content)} bytes)")
                    break

                # JSON response — extract RecordingUrl
                try:
                    rec_data = rec_resp.json()
                    call_obj = rec_data.get("Call", {})
                    remote_url = (
                        rec_data.get("Recording", {}).get("RecordingUrl") or
                        rec_data.get("RecordingUrl") or
                        call_obj.get("RecordingUrl")
                    )
                    if not remote_url or remote_url.strip() == "":
                        remote_url = None
                except Exception:
                    remote_url = None

                if remote_url:
                    ws_logger.info(f"[RECORDING] Got URL: {remote_url}, downloading...")
                    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as _hc2:
                        audio_resp = await _hc2.get(remote_url, headers={"Authorization": f"Basic {auth_b64}"})
                    if audio_resp.status_code == 200 and len(audio_resp.content) > 1000:
                        _rec_dir = os.path.join(os.path.dirname(__file__), "recordings")
                        os.makedirs(_rec_dir, exist_ok=True)
                        ext = "wav" if "wav" in audio_resp.headers.get("content-type", "") else "mp3"
                        _rec_fname = f"call_{_call_lead_id}_{int(_call_start_time)}.{ext}"
                        _rec_path = os.path.join(_rec_dir, _rec_fname)
                        with open(_rec_path, "wb") as f:
                            f.write(audio_resp.content)
                        recording_url = f"/api/recordings/{_rec_fname}"
                        ws_logger.info(f"[RECORDING] Downloaded: {_rec_path} ({len(audio_resp.content)} bytes)")
                    break
                else:
                    ws_logger.info(f"[RECORDING] No URL yet, retry {_attempt+1}/6, waiting 10s...")
                    await asyncio.sleep(10)

            if not recording_url:
                ws_logger.warning(f"[RECORDING] Exotel recording not available after 6 retries, falling back to server-side recording")
            else:
                ws_logger.warning(f"[RECORDING] Exotel returned {rec_resp.status_code}")
        except Exception as _re:
            ws_logger.error(f"[RECORDING] Error fetching from Exotel: {_re}")

    # --- Server-side recording fallback — merge mic + TTS PCM into WAV ---
    if not recording_url:
        try:
            import struct, wave
            mic_chunks = _recording_mic_chunks
            tts_chunks = _tts_recording_buffers.get(stream_sid, [])
            if mic_chunks or tts_chunks:
                ws_logger.info(f"[RECORDING] Building server-side WAV: {len(mic_chunks)} mic chunks, {len(tts_chunks)} tts chunks")
                SAMPLE_RATE = 8000
                SAMPLE_WIDTH = 2  # 16-bit

                # Find time range
                all_times = [t for t, _ in mic_chunks] + [t for t, _ in tts_chunks]
                if all_times:
                    t_start = min(all_times)
                    t_end = max(all_times) + 0.5
                    total_samples = int((t_end - t_start) * SAMPLE_RATE)

                    # Create stereo buffer: left=user, right=AI
                    user_buf = bytearray(total_samples * SAMPLE_WIDTH)
                    ai_buf = bytearray(total_samples * SAMPLE_WIDTH)

                    for ts, pcm in mic_chunks:
                        offset = int((ts - t_start) * SAMPLE_RATE) * SAMPLE_WIDTH
                        end = offset + len(pcm)
                        if end <= len(user_buf):
                            user_buf[offset:end] = pcm

                    for ts, pcm in tts_chunks:
                        offset = int((ts - t_start) * SAMPLE_RATE) * SAMPLE_WIDTH
                        end = offset + len(pcm)
                        if end <= len(ai_buf):
                            ai_buf[offset:end] = pcm

                    # Interleave into stereo (L=user, R=ai)
                    stereo = bytearray(total_samples * SAMPLE_WIDTH * 2)
                    for i in range(total_samples):
                        src = i * SAMPLE_WIDTH
                        dst = i * SAMPLE_WIDTH * 2
                        stereo[dst:dst+SAMPLE_WIDTH] = user_buf[src:src+SAMPLE_WIDTH]
                        stereo[dst+SAMPLE_WIDTH:dst+SAMPLE_WIDTH*2] = ai_buf[src:src+SAMPLE_WIDTH]

                    _rec_dir = os.path.join(os.path.dirname(__file__), "recordings")
                    os.makedirs(_rec_dir, exist_ok=True)
                    _rec_fname = f"call_{_call_lead_id}_{int(_call_start_time)}.wav"
                    _rec_path = os.path.join(_rec_dir, _rec_fname)

                    with wave.open(_rec_path, 'wb') as wf:
                        wf.setnchannels(2)
                        wf.setsampwidth(SAMPLE_WIDTH)
                        wf.setframerate(SAMPLE_RATE)
                        wf.writeframes(bytes(stereo))

                    recording_url = f"/api/recordings/{_rec_fname}"
                    ws_logger.info(f"[RECORDING] Server-side WAV saved: {_rec_path} ({len(stereo)} bytes, {round(total_samples/SAMPLE_RATE, 1)}s)")
        except Exception as _wav_err:
            ws_logger.error(f"[RECORDING] Server-side WAV error: {_wav_err}")

    # --- Save transcript to DB ---
    call_duration = round(time.time() - _call_start_time, 1)
    if transcript_turns:
        save_call_transcript(
            lead_id=_call_lead_id,
            transcript_json=json.dumps(transcript_turns, ensure_ascii=False),
            recording_url=recording_url,
            call_duration_s=call_duration,
            campaign_id=_campaign_id,
        )
