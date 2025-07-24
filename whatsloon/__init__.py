"""
whatsloon package initialization.

This module exposes the main WhatsAppCloudAPIClient class, which combines all
WhatsApp Cloud API functionalities.
"""

from .base import WhatsAppBaseClient
from .address import AddressSender
from .audio import AudioSender
from .contact import ContactSender
from .contextual_reply import ContextualReply
from .cta import CTASender
from .document import DocumentSender
from .flow import FlowSender
from .image import ImageSender
from .location_request import LocationRequestSender
from .location import LocationSender
from .reaction import ReactionSender
from .read_receipts import ReadMark
from .reply_buttons import ReplyButtonSender
from .sticker import StickerSender
from .template import TemplateSender
from .text import TextSender
from .typing_indicator import TypingIndicator
from .video import VideoSender



# Expose all mixins for custom client composition
__all__ = [
    "WhatsAppBaseClient",
    "AddressSender",
    "AudioSender",
    "ContactSender",
    "ContextualReply",
    "CTASender",
    "DocumentSender",
    "FlowSender",
    "ImageSender",
    "LocationRequestSender",
    "LocationSender",
    "ReactionSender",
    "ReadMark",
    "ReplyButtonSender",
    "StickerSender",
    "TemplateSender",
    "TextSender",
    "TypingIndicator",
    "VideoSender",
    "WhatsAppCloudAPIClient",
]

class WhatsAppCloudAPIClient(
    WhatsAppBaseClient,
    AddressSender,
    AudioSender,
    ContactSender,
    ContextualReply,
    CTASender,
    DocumentSender,
    FlowSender,
    ImageSender,
    LocationRequestSender,
    LocationSender,
    ReactionSender,
    ReadMark,
    ReplyButtonSender,
    StickerSender,
    TemplateSender,
    TextSender,
    TypingIndicator,
    VideoSender,
):
    """
    Main client for WhatsApp Cloud API.

    - Use this class directly for all WhatsApp features:
        >>> from whatsloon import WhatsAppCloudAPIClient
        >>> client = WhatsAppCloudAPIClient(...)
        >>> client.send_text_message("Hello!")

    - Or compose your own client with only the mixins you need:
        >>> from whatsloon import WhatsAppBaseClient, TextSender, ImageSender
        >>> class MyClient(WhatsAppBaseClient, TextSender, ImageSender):
        ...     pass
        >>> client = MyClient(...)
        >>> client.send_text_message("Hi!")

    All mixins are available for import from the package root.
    """
    pass
