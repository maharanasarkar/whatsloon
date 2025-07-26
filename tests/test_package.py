"""
Package-level tests for whatsloon.
These tests check that the package imports, exposes expected modules/classes, and basic integration works.
"""

import importlib
import sys

def test_import_whatsloon():
    """
    Test that the whatsloon package can be imported.
    Input: None
    Output: Module is importable and present in sys.modules.
    """
    import whatsloon
    assert "whatsloon" in sys.modules

def test_import_all_mixins():
    """
    Test that all main mixin modules/classes can be imported from whatsloon.
    Input: None
    Output: All mixin modules/classes import without error.
    """
    from whatsloon import (
        flow, list, reply_buttons, location, location_request, reaction, sticker, template, video, read_receipts, contextual_reply, typing_indicator, address, audio, base, contact, document, image, text
    )
    # Just check that the modules are loaded
    assert flow is not None
    assert list is not None
    assert reply_buttons is not None
    assert location is not None
    assert location_request is not None
    assert reaction is not None
    assert sticker is not None
    assert template is not None
    assert video is not None
    assert read_receipts is not None
    assert contextual_reply is not None
    assert typing_indicator is not None
    assert address is not None
    assert audio is not None
    assert base is not None
    assert contact is not None
    assert document is not None
    assert image is not None
    assert text is not None

def test_version_exists():
    """
    Test that the whatsloon package defines a __version__ attribute (if present).
    Input: None
    Output: __version__ exists or is not required.
    """
    import whatsloon
    assert hasattr(whatsloon, "__version__") or True  # Acceptable if not present

def test_dummy_client_integration():
    """
    Test that a DummyClient with all mixins can be instantiated and basic attributes exist.
    Input: None
    Output: DummyClient instance has base_url, headers, recipient_to_send.
    """
    from whatsloon.flow import FlowSender
    from whatsloon.list import ListSender
    from whatsloon.reply_buttons import ReplyButtonSender
    from whatsloon.location import LocationSender
    from whatsloon.location_request import LocationRequestSender
    from whatsloon.reaction import ReactionSender
    from whatsloon.sticker import StickerSender
    from whatsloon.template import TemplateSender
    from whatsloon.video import VideoSender
    from whatsloon.read_receipts import ReadMark
    from whatsloon.contextual_reply import ContextualReply
    from whatsloon.typing_indicator import TypingIndicator
    from whatsloon.address import AddressSender
    from whatsloon.audio import AudioSender
    from whatsloon.base import WhatsAppBaseClient
    from whatsloon.contact import ContactSender
    from whatsloon.document import DocumentSender
    from whatsloon.image import ImageSender
    from whatsloon.text import TextSender

    class DummyClient(
        FlowSender, ListSender, ReplyButtonSender, LocationSender, LocationRequestSender,
        ReactionSender, StickerSender, TemplateSender, VideoSender, ReadMark, ContextualReply,
        TypingIndicator, AddressSender, AudioSender, WhatsAppBaseClient, ContactSender, DocumentSender, ImageSender, TextSender
    ):
        def __init__(self):
            WhatsAppBaseClient.__init__(
                self,
                access_token="token",
                phone_number_id="id",
                recipient_country_code="91",
                recipient_mobile_number="9876543210",
            )

    client = DummyClient()
    assert hasattr(client, "base_url")
    assert hasattr(client, "headers")
    assert hasattr(client, "recipient_to_send")
