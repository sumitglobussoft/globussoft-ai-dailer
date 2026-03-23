import React, { useState, useRef, useEffect } from 'react';

export default function Sandbox({ apiUrl }) {
  const [recording, setRecording] = useState(false);
  const [transcripts, setTranscripts] = useState([]);
  const wsRef = useRef(null);
  const audioContextRef = useRef(null);
  const sourceRef = useRef(null);
  const processorRef = useRef(null);

  const startSandbox = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const wsUrl = apiUrl.replace("http", "ws") + `/ws/sandbox`;
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => setRecording(true);
      
      wsRef.current.onmessage = async (e) => {
        const data = JSON.parse(e.data);
        if (data.type === 'transcript') {
          setTranscripts(prev => [...prev, data]);
        } else if (data.type === 'audio') {
          // Decode B64 MP3 chunk and play
          try {
            const binaryStr = window.atob(data.payload);
            const len = binaryStr.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) bytes[i] = binaryStr.charCodeAt(i);
            
            // In a real flawless production app we would use MediaSourceBuffer to append exact chunks instantly.
            // Using a simple Blob URL here for simplicity which might have tiny micro-gaps, but suffices for Sandbox testing.
            const blob = new Blob([bytes], { type: 'audio/mp3' });
            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);
            audio.play();
          } catch(e) {}
        }
      };

      const audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
      audioContextRef.current = audioContext;
      const source = audioContext.createMediaStreamSource(stream);
      sourceRef.current = source;
      
      // We create a script processor to capture PCM samples and stream them out
      const processor = audioContext.createScriptProcessor(2048, 1, 1);
      processorRef.current = processor;
      
      processor.onaudioprocess = (e) => {
        const inputData = e.inputBuffer.getChannelData(0);
        // Convert Float32Array to Int16Array
        const int16Buffer = new Int16Array(inputData.length);
        for (let i = 0; i < inputData.length; i++) {
          const s = Math.max(-1, Math.min(1, inputData[i]));
          int16Buffer[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
        }
        
        // Convert Int16Array to Base64 String to send as JSON payload
        const bytes = new Uint8Array(int16Buffer.buffer);
        let binaryStr = '';
        for (let i = 0; i < bytes.byteLength; i++) {
          binaryStr += String.fromCharCode(bytes[i]);
        }
        const b64 = window.btoa(binaryStr);
        
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
          wsRef.current.send(JSON.stringify({ type: 'audio_chunk', payload: b64 }));
        }
      };

      source.connect(processor);
      processor.connect(audioContext.destination);
    } catch (e) {
      console.error("Sandbox initialization failed", e);
    }
  };

  const stopSandbox = () => {
    setRecording(false);
    if (processorRef.current && sourceRef.current) {
      sourceRef.current.disconnect();
      processorRef.current.disconnect();
    }
    if (wsRef.current) wsRef.current.close();
  };

  return (
    <div className="glass-panel" style={{padding: '2rem'}}>
      <h2 style={{marginTop: 0, marginBottom: '0.5rem', color: '#f8fafc'}}>🎯 AI Training Sandbox</h2>
      <p style={{color: '#94a3b8', marginBottom: '2rem'}}>Roleplay and stress test the core Voice Agent engine using your computer microphone. Ensure the system perfectly handles complex objections before deploying to live telecom routes.</p>
      
      <div style={{display: 'flex', gap: '2rem'}}>
        <div style={{background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', padding: '1.5rem', flex: 1}}>
          <h3 style={{marginTop: 0, color: '#e2e8f0'}}>Simulation Controls</h3>
          <div style={{display: 'flex', gap: '1rem', marginTop: '1.5rem'}}>
            {!recording ? (
              <button className="btn-primary" onClick={startSandbox} style={{background: '#22c55e', borderColor: '#22c55e'}}>🎙️ Start Mic Simulation</button>
            ) : (
              <button className="btn-call" style={{borderColor: '#ef4444', color: '#ef4444'}} onClick={stopSandbox}>⏹️ Stop Simulation</button>
            )}
            <button className="btn-call" onClick={() => setTranscripts([])}>🗑️ Clear Logs</button>
          </div>
          
          <div style={{background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '1rem', marginTop: '1.5rem', flexGrow: 1}}>
            <h4 style={{marginTop: 0}}>Sandbox State:</h4>
            <ul style={{color: '#94a3b8', fontSize: '0.9rem', lineHeight: 1.6}}>
              <li>Model: Gemini 2.5 Flash</li>
              <li>Instructions: Hard Evaluation Mode</li>
              <li>Microphone: {recording ? <span style={{color: '#34d399'}}>Active 🟢</span> : <span style={{color: '#ef4444'}}>Inactive 🔴</span>}</li>
              <li>TTS Streams: ElevenLabs HTTP</li>
            </ul>
          </div>
        </div>

        <div style={{background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', padding: '1.5rem', flex: 2}}>
          <h3 style={{marginTop: 0, color: '#e2e8f0'}}>Diagnostic Transcripts</h3>
          <div style={{background: 'rgba(0,0,0,0.3)', borderRadius: '8px', padding: '1.5rem', minHeight: '300px', display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto'}}>
            {transcripts.length === 0 && <p style={{color: '#64748b', textAlign: 'center', marginTop: '4rem'}}>Waiting for audio...</p>}
            {transcripts.map((t, idx) => (
              <div key={idx} style={{
                alignSelf: t.role === 'user' ? 'flex-start' : 'flex-end',
                background: t.role === 'user' ? 'rgba(56, 189, 248, 0.1)' : 'rgba(168, 85, 247, 0.1)',
                padding: '10px 16px', borderRadius: '8px',
                color: t.role === 'user' ? '#e0f2fe' : '#f3e8ff',
                maxWidth: '80%', border: `1px solid ${t.role === 'user' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(168, 85, 247, 0.2)'}`
              }}>
                <strong style={{display: 'block', fontSize: '0.75rem', textTransform: 'uppercase', marginBottom: '4px', opacity: 0.7}}>{t.role === 'user' ? 'Sales Manager (You)' : 'AI Agent Simulator'}</strong>
                {t.text}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
