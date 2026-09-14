from __future__ import annotations

import pytest

from . import config
from .webhook import authorize_query_token, build_registration_payload, parse_delivery, parse_message


def test_verified_inventory_listener_is_exposed():
    assert config.is_inventory_listener("+91 79751 02130")
    assert config.is_inventory_listener("919902024973")
    assert not config.is_inventory_listener("919148338801")


def test_webhook_token_is_constant_time_validated():
    assert authorize_query_token({"t": "secret"}, "secret")
    assert not authorize_query_token({"t": "wrong"}, "secret")
    assert not authorize_query_token({}, "secret")


def test_registration_requires_explicit_event_selection():
    payload = build_registration_payload(
        "https://example.test/hook/",
        ["messages", {"type": "statuses", "method": "post"}],
    )
    assert payload["webhooks"][0]["url"] == "https://example.test/hook"
    assert payload["webhooks"][0]["events"] == [
        {"type": "messages", "method": "post"},
        {"type": "statuses", "method": "post"},
    ]
    with pytest.raises(ValueError):
        build_registration_payload("https://example.test/hook", [])


def test_text_message_is_normalized():
    message = parse_message({
        "id": "m1",
        "chat_id": "919148338801@s.whatsapp.net",
        "from": "919148338801",
        "from_name": "Ramesh",
        "from_me": False,
        "type": "text",
        "text": {"body": "Looking for 2BHK"},
        "timestamp": 1,
    })
    assert message.message_id == "m1"
    assert message.body == "Looking for 2BHK"
    assert not message.is_group
    assert not message.is_inventory_listener


def test_location_and_media_are_not_lost():
    message = parse_message({
        "id": "m2",
        "chat_id": "917975102130@s.whatsapp.net",
        "from": "917975102130",
        "from_me": False,
        "type": "image",
        "image": {"caption": "3BHK", "link": "https://media.example/x"},
        "location": {"latitude": 12.91, "longitude": 77.64},
    })
    assert message.has_media
    assert message.media_reference == "https://media.example/x"
    assert "maps.google.com" in message.body
    assert message.is_inventory_listener


def test_delivery_caps_and_ignores_invalid_entries():
    payload = {"messages": [{"id": "m1", "chat_id": "x", "from": "x"}, "bad"] * 60}
    messages = parse_delivery(payload)
    assert len(messages) == 60
