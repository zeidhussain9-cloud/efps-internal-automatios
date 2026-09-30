from shared.whatsapp_whapi import config
from shared.whatsapp_whapi.webhook import parse_delivery, parse_message

def test_verified_inventory_sources_are_data_only():
    assert config.normalise_phone("+91 79751 02130") in config.INVENTORY_SOURCE_NUMBERS
    assert config.normalise_phone("919902024973") in config.INVENTORY_SOURCE_NUMBERS
    assert config.normalise_phone("919148338801") not in config.INVENTORY_SOURCE_NUMBERS

def test_parser_is_transport_only():
    message=parse_message({"id":"m1","chat_id":"919148338801@s.whatsapp.net","from":"919148338801","from_me":False,"type":"text","text":{"body":"hello"},"timestamp":1})
    assert message.message_id=="m1"
    assert message.body=="hello"
    assert message.is_group is False
    assert not hasattr(message,"listener")
    assert not hasattr(message,"is_inventory_listener")
    assert not hasattr(message,"is_lead_listener")

def test_delivery_parses_messages_without_business_classification():
    parsed=parse_delivery({"messages":[{"id":"m1","chat_id":"919148338801@s.whatsapp.net","from":"919148338801","type":"text","text":{"body":"hello"}}]})
    assert len(parsed)==1
    assert parsed[0].message_type=="text"
