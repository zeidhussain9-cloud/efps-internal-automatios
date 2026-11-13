from __future__ import annotations

import webhook_handler
import inventory_runtime


def test_whapi_inventory_sender_routes_to_inventory_runtime(monkeypatch):
    monkeypatch.setenv("INVENTORY_SENDERS", "917975102130,919902024973")
    monkeypatch.setattr(webhook_handler, "GoogleSheetsClient", lambda: object())
    routed = []
    monkeypatch.setattr(
        inventory_runtime,
        "handle",
        lambda message, *, client: routed.append((message.sender, client)) or {"inventory": True},
    )
    payload = {
        "messages": [{
            "id": "inventory-message-1",
            "chat_id": "917975102130@s.whatsapp.net",
            "from": "917975102130",
            "from_me": False,
            "type": "text",
            "text": {"body": "NEW"},
            "timestamp": 1794528000,
        }]
    }

    result = webhook_handler.process(payload)

    assert result["handled"] == 1
    assert result["results"] == [{"inventory": True}]
    assert len(routed) == 1
    assert routed[0][0] == "917975102130"


def test_whapi_lead_sender_does_not_enter_inventory_runtime(monkeypatch):
    monkeypatch.setenv("INVENTORY_SENDERS", "917975102130,919902024973")
    monkeypatch.setattr(webhook_handler, "GoogleSheetsClient", lambda: object())
    monkeypatch.setattr(webhook_handler, "handle_lead", lambda message: {"lead": message.sender})
    monkeypatch.setattr(
        inventory_runtime,
        "handle",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("inventory route must not run")),
    )
    payload = {
        "messages": [{
            "id": "lead-message-1",
            "chat_id": "919148338801@s.whatsapp.net",
            "from": "919148338801",
            "from_me": False,
            "type": "text",
            "text": {"body": "Looking for a 2 BHK"},
            "timestamp": 1794528000,
        }]
    }

    result = webhook_handler.process(payload)

    assert result["results"] == [{"lead": "919148338801"}]
