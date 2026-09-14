"""Stage-1 inventory webhook adapter for the two dedicated listener numbers."""
from __future__ import annotations
from .intake import ingest, InMemorySessionStore
from .pipeline import initial_row, next_listing_id, process_closed_session, write_new_property, write_phase1_update
from shared.google_sheets import schema

DEFAULT_STORE = InMemorySessionStore()


def _value(message, key, default=""):
    return getattr(message, key, default) if hasattr(message, key) else message.get(key, default)


def _find_row(client, listing_id):
    rows = client.read_range(schema.SHEET_ID, schema.WORKSHEET_NAME, "A2:A")
    for i, row in enumerate(rows, start=2):
        if row and str(row[0]).strip() == listing_id:
            return i
    return None


def _persist_raw(client, session):
    row_number = _find_row(client, session.listing_id)
    if row_number is None:
        raise RuntimeError(f"listing_id not found: {session.listing_id}")
    # raw_message_text is G in the latest contract. intake_status remains Raw
    # until the completed property is processed.
    client.write_range(
        schema.SHEET_ID,
        schema.WORKSHEET_NAME,
        schema.range_for("raw_message_text", "raw_message_text", row_number),
        [[session.raw_text]],
    )


def handle(message, *, store=None, sheets_client=None, maps_client=None, ai_llm=None):
    """Process one normalized WhAPI inventory message through Stages 1 and 2."""
    store = store or DEFAULT_STORE
    state, session = ingest(message, store)

    if state == "opened" and sheets_client is not None:
        session.listing_id = next_listing_id(sheets_client)
        session.source_group = str(_value(message, "chat_id"))
        store.put(session)
        write_new_property(
            sheets_client,
            initial_row(
                session.listing_id,
                source_group=session.source_group,
                onboarded_on=session.started_at,
            ),
        )
        return {"state": "opened", "listing_id": session.listing_id}

    if state == "collecting" and sheets_client is not None:
        _persist_raw(sheets_client, session)
        return {"state": "collecting", "listing_id": session.listing_id, "image_count": session.image_count}

    if state != "closed":
        return {"state": state}
    if sheets_client is None:
        return {"state": "closed", "raw_text": session.raw_text, "image_count": session.image_count}

    row_number = _find_row(sheets_client, session.listing_id)
    if row_number is None:
        raise RuntimeError(f"closed session row missing: {session.listing_id}")

    current = sheets_client.read_range(
        schema.SHEET_ID,
        schema.WORKSHEET_NAME,
        schema.full_range(row_number),
    )
    if not current:
        raise RuntimeError(f"closed session row unreadable: {session.listing_id}")
    existing = schema.row_to_mapping(current[0])
    existing["raw_message_text"] = session.raw_text

    processed, issues = process_closed_session(
        session.raw_text,
        row=existing,
        maps_client=maps_client,
        ai_llm=ai_llm,
    )
    write_phase1_update(sheets_client, row_number, processed)
    return {
        "state": "processed",
        "listing_id": session.listing_id,
        "issues": issues,
        "image_count": session.image_count,
    }
