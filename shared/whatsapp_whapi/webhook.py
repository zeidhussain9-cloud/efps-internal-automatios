"""Reusable WhAPI webhook transport primitives.

This layer only normalizes provider payloads. Lead creation, conversation
append, inventory workflows and other business decisions live outside it.
"""

from __future__ import annotations

import hmac
from dataclasses import dataclass
from typing import Any, Mapping

from . import config


@dataclass(frozen=True)
class IncomingMessage:
    message_id: str
    chat_id: str
    sender: str
    sender_name: str
    from_me: bool
    message_type: str
    body: str
    media_reference: str
    timestamp: Any

    @property
    def is_group(self) -> bool:
        return self.chat_id.endswith("@g.us")

    @property
    def has_media(self) -> bool:
        return bool(self.media_reference) or self.message_type in {
            "image", "video", "document", "audio"
        }



def parse_message(raw: Mapping[str, Any]) -> IncomingMessage:
    """Normalize one WhAPI message across common text/media/location forms."""
    message_type = raw.get("type") if isinstance(raw.get("type"), str) else "text"
    chat_id = str(raw.get("chat_id") or "")
    sender = str(raw.get("from") or "")
    body = ""
    media_reference = ""

    text = raw.get("text")
    if isinstance(text, Mapping):
        body = str(text.get("body") or "")
    elif isinstance(text, str):
        body = text

    preview = raw.get("link_preview")
    if isinstance(preview, Mapping):
        preview_body = str(preview.get("body") or "")
        url = str(preview.get("url") or "")
        title = str(preview.get("title") or "").strip()
        body = body or preview_body
        if url and url not in body:
            body = f"{body}\n{url}".strip()
        if title and title not in body:
            body = f"{body}\nMaps place name: {title}".strip()

    for location_key in ("location", "live_location"):
        location = raw.get(location_key)
        if isinstance(location, Mapping):
            lat = location.get("latitude")
            lng = location.get("longitude")
            if lat is not None and lng is not None:
                link = f"https://maps.google.com/?q={lat},{lng}"
                body = f"{body}\n{link}".strip() if body else link
                break

    for media_key in ("image", "video", "document", "audio"):
        media = raw.get(media_key)
        if isinstance(media, Mapping):
            body = body or str(media.get("caption") or "")
            media_reference = str(media.get("link") or media.get("id") or "")
            break

    return IncomingMessage(
        message_id=str(raw.get("id") or ""),
        chat_id=chat_id,
        sender=sender,
        sender_name=str(raw.get("from_name") or ""),
        from_me=bool(raw.get("from_me")),
        message_type=message_type,
        body=body[:4000],
        media_reference=media_reference,
        timestamp=raw.get("timestamp"),
    )


def parse_delivery(payload: Mapping[str, Any]) -> tuple[IncomingMessage, ...]:
    """Return valid messages from a webhook body, capped defensively."""
    messages = payload.get("messages")
    if not isinstance(messages, list):
        return ()
    parsed: list[IncomingMessage] = []
    for item in messages:
        if not isinstance(item, Mapping) or not str(item.get("id") or ""):
            continue
        parsed.append(parse_message(item))
        if len(parsed) >= 100:
            break
    return tuple(parsed)


def authorize_query_token(query: Mapping[str, Any] | None, expected: str) -> bool:
    """Constant-time validation of the legacy `?t=` webhook token."""
    if not expected:
        return False
    supplied = str((query or {}).get(config.WEBHOOK_QUERY_PARAMETER, ""))
    return hmac.compare_digest(supplied, expected)


def build_registration_payload(url: str, events: list[Mapping[str, str] | str]) -> dict[str, Any]:
    """Build webhook settings without performing a live mutation."""
    return config.webhook_registration_payload(url, events)
