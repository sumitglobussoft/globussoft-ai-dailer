"""
Pluggable WhatsApp provider abstraction for the AI Dialer.

Supports:
- gupshup: Gupshup WhatsApp Business API
- wati: WATI (WhatsApp Team Inbox)
- aisensei: AiSensei WhatsApp API
- interakt: Interakt WhatsApp API
- meta: Meta Cloud API (direct)

Usage:
    provider = get_wa_provider("gupshup", apikey="...", source_phone="...")
    result = await provider.send_text("+919876543210", "Hello!")
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
import httpx
import hmac
import hashlib
import logging
import json

logger = logging.getLogger("uvicorn.error")


@dataclass
class WaIncomingMessage:
    provider_message_id: str
    sender_phone: str
    sender_name: Optional[str]
    message_type: str  # text, image, document, audio
    text: Optional[str]
    media_url: Optional[str]
    timestamp: str
    raw_payload: dict


@dataclass
class WaSendResult:
    success: bool
    provider_message_id: Optional[str]
    error: Optional[str]


class BaseWaProvider(ABC):
    def __init__(self, **config):
        self.config = config

    @abstractmethod
    async def send_text(self, to_phone: str, text: str) -> WaSendResult:
        pass

    @abstractmethod
    async def send_template(self, to_phone: str, template_name: str, language: str, parameters: List[str]) -> WaSendResult:
        pass

    @abstractmethod
    async def send_media(self, to_phone: str, media_type: str, media_url: str, caption: Optional[str] = None) -> WaSendResult:
        pass

    @abstractmethod
    def validate_webhook(self, request_headers: dict, request_body: bytes) -> bool:
        pass

    @abstractmethod
    def parse_incoming_message(self, payload: dict) -> Optional[WaIncomingMessage]:
        pass

    @abstractmethod
    async def mark_as_read(self, message_id: str) -> bool:
        pass


# ─── Gupshup Provider ──────────────────────────────────────────────────────────

class GupshupProvider(BaseWaProvider):

    SEND_URL = "https://api.gupshup.io/wa/api/v1/msg"

    async def send_text(self, to_phone: str, text: str) -> WaSendResult:
        apikey = self.config.get("apikey", "")
        source = self.config.get("source_phone", "")
        payload = {
            "channel": "whatsapp",
            "source": source,
            "destination": to_phone,
            "message": json.dumps({"type": "text", "text": text}),
            "src.name": self.config.get("app_name", "callified"),
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self.SEND_URL, data=payload, headers={"apikey": apikey})
                data = resp.json()
            if resp.status_code == 200 and data.get("status") == "submitted":
                return WaSendResult(success=True, provider_message_id=data.get("messageId"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"Gupshup send_text error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    async def send_template(self, to_phone: str, template_name: str, language: str, parameters: List[str]) -> WaSendResult:
        apikey = self.config.get("apikey", "")
        source = self.config.get("source_phone", "")
        template_msg = {
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": [{"type": "body", "parameters": [{"type": "text", "text": p} for p in parameters]}] if parameters else [],
            },
        }
        payload = {
            "channel": "whatsapp",
            "source": source,
            "destination": to_phone,
            "message": json.dumps(template_msg),
            "src.name": self.config.get("app_name", "callified"),
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self.SEND_URL, data=payload, headers={"apikey": apikey})
                data = resp.json()
            if resp.status_code == 200 and data.get("status") == "submitted":
                return WaSendResult(success=True, provider_message_id=data.get("messageId"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"Gupshup send_template error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    async def send_media(self, to_phone: str, media_type: str, media_url: str, caption: Optional[str] = None) -> WaSendResult:
        apikey = self.config.get("apikey", "")
        source = self.config.get("source_phone", "")
        msg = {"type": media_type, media_type: {"url": media_url}}
        if caption:
            msg[media_type]["caption"] = caption
        payload = {
            "channel": "whatsapp",
            "source": source,
            "destination": to_phone,
            "message": json.dumps(msg),
            "src.name": self.config.get("app_name", "callified"),
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self.SEND_URL, data=payload, headers={"apikey": apikey})
                data = resp.json()
            if resp.status_code == 200 and data.get("status") == "submitted":
                return WaSendResult(success=True, provider_message_id=data.get("messageId"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"Gupshup send_media error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    def validate_webhook(self, request_headers: dict, request_body: bytes) -> bool:
        # Gupshup does not use HMAC verification; rely on IP allowlist or token
        return True

    def parse_incoming_message(self, payload: dict) -> Optional[WaIncomingMessage]:
        try:
            inner = payload.get("payload", {})
            msg_payload = inner.get("payload", {})
            msg_type = inner.get("type", "text")
            text = msg_payload.get("text") if msg_type == "text" else None
            media_url = msg_payload.get("url") if msg_type != "text" else None
            return WaIncomingMessage(
                provider_message_id=inner.get("id", ""),
                sender_phone=inner.get("source", ""),
                sender_name=inner.get("sender", {}).get("name"),
                message_type=msg_type,
                text=text,
                media_url=media_url,
                timestamp=inner.get("timestamp", ""),
                raw_payload=payload,
            )
        except Exception as e:
            logger.error(f"Gupshup parse error: {e}")
            return None

    async def mark_as_read(self, message_id: str) -> bool:
        # Gupshup auto-marks as read; no explicit API call needed
        return True


# ─── Wati Provider ──────────────────────────────────────────────────────────────

class WatiProvider(BaseWaProvider):

    async def send_text(self, to_phone: str, text: str) -> WaSendResult:
        tenant_url = self.config.get("tenant_url", "").rstrip("/")
        token = self.config.get("api_token", "")
        url = f"{tenant_url}/api/v1/sendSessionMessage/{to_phone}"
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json={"messageText": text},
                                         headers={"Authorization": f"Bearer {token}"})
                data = resp.json()
            if resp.status_code == 200 and data.get("result"):
                return WaSendResult(success=True, provider_message_id=data.get("id"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"Wati send_text error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    async def send_template(self, to_phone: str, template_name: str, language: str, parameters: List[str]) -> WaSendResult:
        tenant_url = self.config.get("tenant_url", "").rstrip("/")
        token = self.config.get("api_token", "")
        url = f"{tenant_url}/api/v1/sendTemplateMessage/{to_phone}"
        body = {
            "template_name": template_name,
            "broadcast_name": "callified_broadcast",
            "parameters": [{"name": f"body_{i+1}", "value": p} for i, p in enumerate(parameters)],
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=body, headers={"Authorization": f"Bearer {token}"})
                data = resp.json()
            if resp.status_code == 200 and data.get("result"):
                return WaSendResult(success=True, provider_message_id=data.get("id"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"Wati send_template error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    async def send_media(self, to_phone: str, media_type: str, media_url: str, caption: Optional[str] = None) -> WaSendResult:
        tenant_url = self.config.get("tenant_url", "").rstrip("/")
        token = self.config.get("api_token", "")
        url = f"{tenant_url}/api/v1/sendSessionFile/{to_phone}"
        body = {"url": media_url, "caption": caption or ""}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=body, headers={"Authorization": f"Bearer {token}"})
                data = resp.json()
            if resp.status_code == 200 and data.get("result"):
                return WaSendResult(success=True, provider_message_id=data.get("id"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"Wati send_media error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    def validate_webhook(self, request_headers: dict, request_body: bytes) -> bool:
        # Wati uses webhook URL verification only
        return True

    def parse_incoming_message(self, payload: dict) -> Optional[WaIncomingMessage]:
        try:
            msg_type = payload.get("type", "text")
            text = payload.get("text") if msg_type == "text" else None
            media_url = payload.get("data", {}).get("url") if msg_type != "text" else None
            return WaIncomingMessage(
                provider_message_id=payload.get("id", ""),
                sender_phone=payload.get("waId", ""),
                sender_name=payload.get("senderName"),
                message_type=msg_type,
                text=text,
                media_url=media_url,
                timestamp=payload.get("timestamp", ""),
                raw_payload=payload,
            )
        except Exception as e:
            logger.error(f"Wati parse error: {e}")
            return None

    async def mark_as_read(self, message_id: str) -> bool:
        return True


# ─── AiSensei Provider ─────────────────────────────────────────────────────────

class AiSenseiProvider(BaseWaProvider):

    async def send_text(self, to_phone: str, text: str) -> WaSendResult:
        base_url = self.config.get("base_url", "").rstrip("/")
        api_key = self.config.get("api_key", "")
        url = f"{base_url}/api/v1/messages"
        body = {"to": to_phone, "type": "text", "text": {"body": text}}
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=body, headers={"X-API-Key": api_key})
                data = resp.json()
            if resp.status_code in (200, 201):
                return WaSendResult(success=True, provider_message_id=data.get("messageId") or data.get("id"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"AiSensei send_text error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    async def send_template(self, to_phone: str, template_name: str, language: str, parameters: List[str]) -> WaSendResult:
        base_url = self.config.get("base_url", "").rstrip("/")
        api_key = self.config.get("api_key", "")
        url = f"{base_url}/api/v1/messages"
        body = {
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": [{"type": "body", "parameters": [{"type": "text", "text": p} for p in parameters]}] if parameters else [],
            },
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=body, headers={"X-API-Key": api_key})
                data = resp.json()
            if resp.status_code in (200, 201):
                return WaSendResult(success=True, provider_message_id=data.get("messageId") or data.get("id"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"AiSensei send_template error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    async def send_media(self, to_phone: str, media_type: str, media_url: str, caption: Optional[str] = None) -> WaSendResult:
        base_url = self.config.get("base_url", "").rstrip("/")
        api_key = self.config.get("api_key", "")
        url = f"{base_url}/api/v1/messages"
        body = {"to": to_phone, "type": media_type, media_type: {"link": media_url}}
        if caption:
            body[media_type]["caption"] = caption
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(url, json=body, headers={"X-API-Key": api_key})
                data = resp.json()
            if resp.status_code in (200, 201):
                return WaSendResult(success=True, provider_message_id=data.get("messageId") or data.get("id"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"AiSensei send_media error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    def validate_webhook(self, request_headers: dict, request_body: bytes) -> bool:
        return True

    def parse_incoming_message(self, payload: dict) -> Optional[WaIncomingMessage]:
        try:
            msg_type = payload.get("type", "text")
            text = payload.get("text", {}).get("body") if msg_type == "text" else None
            media_url = payload.get(msg_type, {}).get("link") if msg_type != "text" else None
            return WaIncomingMessage(
                provider_message_id=payload.get("id", ""),
                sender_phone=payload.get("from", "") or payload.get("waId", ""),
                sender_name=payload.get("senderName") or payload.get("profile", {}).get("name"),
                message_type=msg_type,
                text=text,
                media_url=media_url,
                timestamp=payload.get("timestamp", ""),
                raw_payload=payload,
            )
        except Exception as e:
            logger.error(f"AiSensei parse error: {e}")
            return None

    async def mark_as_read(self, message_id: str) -> bool:
        return True


# ─── Interakt Provider ─────────────────────────────────────────────────────────

class InteraktProvider(BaseWaProvider):

    SEND_URL = "https://api.interakt.ai/v1/public/message/"

    async def send_text(self, to_phone: str, text: str) -> WaSendResult:
        api_key = self.config.get("api_key", "")
        # Strip leading + and country code prefix for Interakt
        phone_clean = to_phone.lstrip("+")
        country_code = phone_clean[:2] if len(phone_clean) > 10 else "91"
        phone_number = phone_clean[-10:] if len(phone_clean) > 10 else phone_clean
        body = {
            "countryCode": f"+{country_code}",
            "phoneNumber": phone_number,
            "type": "Text",
            "data": {"message": text},
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self.SEND_URL, json=body,
                                         headers={"Authorization": f"Basic {api_key}", "Content-Type": "application/json"})
                data = resp.json()
            if resp.status_code in (200, 201) and data.get("result"):
                return WaSendResult(success=True, provider_message_id=data.get("id"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"Interakt send_text error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    async def send_template(self, to_phone: str, template_name: str, language: str, parameters: List[str]) -> WaSendResult:
        api_key = self.config.get("api_key", "")
        phone_clean = to_phone.lstrip("+")
        country_code = phone_clean[:2] if len(phone_clean) > 10 else "91"
        phone_number = phone_clean[-10:] if len(phone_clean) > 10 else phone_clean
        body = {
            "countryCode": f"+{country_code}",
            "phoneNumber": phone_number,
            "type": "Template",
            "template": {
                "name": template_name,
                "languageCode": language,
                "bodyValues": parameters,
            },
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self.SEND_URL, json=body,
                                         headers={"Authorization": f"Basic {api_key}", "Content-Type": "application/json"})
                data = resp.json()
            if resp.status_code in (200, 201) and data.get("result"):
                return WaSendResult(success=True, provider_message_id=data.get("id"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"Interakt send_template error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    async def send_media(self, to_phone: str, media_type: str, media_url: str, caption: Optional[str] = None) -> WaSendResult:
        api_key = self.config.get("api_key", "")
        phone_clean = to_phone.lstrip("+")
        country_code = phone_clean[:2] if len(phone_clean) > 10 else "91"
        phone_number = phone_clean[-10:] if len(phone_clean) > 10 else phone_clean
        body = {
            "countryCode": f"+{country_code}",
            "phoneNumber": phone_number,
            "type": "Image" if media_type == "image" else "Document",
            "data": {"url": media_url, "caption": caption or ""},
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self.SEND_URL, json=body,
                                         headers={"Authorization": f"Basic {api_key}", "Content-Type": "application/json"})
                data = resp.json()
            if resp.status_code in (200, 201) and data.get("result"):
                return WaSendResult(success=True, provider_message_id=data.get("id"), error=None)
            return WaSendResult(success=False, provider_message_id=None, error=data.get("message", str(data)))
        except Exception as e:
            logger.error(f"Interakt send_media error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    def validate_webhook(self, request_headers: dict, request_body: bytes) -> bool:
        return True

    def parse_incoming_message(self, payload: dict) -> Optional[WaIncomingMessage]:
        try:
            data = payload.get("data", {})
            message = data.get("message", {})
            customer = data.get("customer", {})
            msg_type = message.get("type", "text")
            text = message.get("text") if msg_type == "text" else None
            media_url = message.get("url") if msg_type != "text" else None
            return WaIncomingMessage(
                provider_message_id=message.get("id", ""),
                sender_phone=customer.get("phone_number", ""),
                sender_name=customer.get("name"),
                message_type=msg_type,
                text=text,
                media_url=media_url,
                timestamp=message.get("timestamp", ""),
                raw_payload=payload,
            )
        except Exception as e:
            logger.error(f"Interakt parse error: {e}")
            return None

    async def mark_as_read(self, message_id: str) -> bool:
        return True


# ─── Meta Cloud API Provider ───────────────────────────────────────────────────

class MetaCloudProvider(BaseWaProvider):

    API_VERSION = "v21.0"

    def _base_url(self) -> str:
        phone_number_id = self.config.get("phone_number_id", "")
        return f"https://graph.facebook.com/{self.API_VERSION}/{phone_number_id}/messages"

    def _headers(self) -> dict:
        access_token = self.config.get("access_token", "")
        return {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

    async def send_text(self, to_phone: str, text: str) -> WaSendResult:
        body = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": text},
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self._base_url(), json=body, headers=self._headers())
                data = resp.json()
            if resp.status_code in (200, 201):
                msg_id = data.get("messages", [{}])[0].get("id") if data.get("messages") else None
                return WaSendResult(success=True, provider_message_id=msg_id, error=None)
            error = data.get("error", {}).get("message", str(data))
            return WaSendResult(success=False, provider_message_id=None, error=error)
        except Exception as e:
            logger.error(f"Meta send_text error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    async def send_template(self, to_phone: str, template_name: str, language: str, parameters: List[str]) -> WaSendResult:
        body = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language},
                "components": [{"type": "body", "parameters": [{"type": "text", "text": p} for p in parameters]}] if parameters else [],
            },
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self._base_url(), json=body, headers=self._headers())
                data = resp.json()
            if resp.status_code in (200, 201):
                msg_id = data.get("messages", [{}])[0].get("id") if data.get("messages") else None
                return WaSendResult(success=True, provider_message_id=msg_id, error=None)
            error = data.get("error", {}).get("message", str(data))
            return WaSendResult(success=False, provider_message_id=None, error=error)
        except Exception as e:
            logger.error(f"Meta send_template error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    async def send_media(self, to_phone: str, media_type: str, media_url: str, caption: Optional[str] = None) -> WaSendResult:
        media_obj = {"link": media_url}
        if caption:
            media_obj["caption"] = caption
        body = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": media_type,
            media_type: media_obj,
        }
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.post(self._base_url(), json=body, headers=self._headers())
                data = resp.json()
            if resp.status_code in (200, 201):
                msg_id = data.get("messages", [{}])[0].get("id") if data.get("messages") else None
                return WaSendResult(success=True, provider_message_id=msg_id, error=None)
            error = data.get("error", {}).get("message", str(data))
            return WaSendResult(success=False, provider_message_id=None, error=error)
        except Exception as e:
            logger.error(f"Meta send_media error: {e}")
            return WaSendResult(success=False, provider_message_id=None, error=str(e))

    def validate_webhook(self, request_headers: dict, request_body: bytes) -> bool:
        app_secret = self.config.get("app_secret", "")
        if not app_secret:
            return False
        signature = request_headers.get("x-hub-signature-256", "")
        if not signature.startswith("sha256="):
            return False
        expected = hmac.new(app_secret.encode("utf-8"), request_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    def parse_incoming_message(self, payload: dict) -> Optional[WaIncomingMessage]:
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            messages = value.get("messages", [])
            if not messages:
                return None
            msg = messages[0]
            contacts = value.get("contacts", [{}])
            profile_name = contacts[0].get("profile", {}).get("name") if contacts else None
            msg_type = msg.get("type", "text")
            text = msg.get("text", {}).get("body") if msg_type == "text" else None
            media_url = None
            if msg_type in ("image", "document", "audio", "video"):
                media_obj = msg.get(msg_type, {})
                media_url = media_obj.get("url") or media_obj.get("link")
            return WaIncomingMessage(
                provider_message_id=msg.get("id", ""),
                sender_phone=msg.get("from", ""),
                sender_name=profile_name,
                message_type=msg_type,
                text=text,
                media_url=media_url,
                timestamp=msg.get("timestamp", ""),
                raw_payload=payload,
            )
        except Exception as e:
            logger.error(f"Meta parse error: {e}")
            return None

    async def mark_as_read(self, message_id: str) -> bool:
        phone_number_id = self.config.get("phone_number_id", "")
        url = f"https://graph.facebook.com/{self.API_VERSION}/{phone_number_id}/messages"
        body = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(url, json=body, headers=self._headers())
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Meta mark_as_read error: {e}")
            return False


# ─── Factory ───────────────────────────────────────────────────────────────────

_PROVIDERS = {
    "gupshup": GupshupProvider,
    "wati": WatiProvider,
    "aisensei": AiSenseiProvider,
    "interakt": InteraktProvider,
    "meta": MetaCloudProvider,
}


def get_wa_provider(provider_name: str, **config) -> BaseWaProvider:
    cls = _PROVIDERS.get(provider_name.lower())
    if not cls:
        raise ValueError(f"Unknown WhatsApp provider: {provider_name}")
    return cls(**config)
