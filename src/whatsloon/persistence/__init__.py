"""Persistence package."""

from whatsloon.persistence.base import (
    ConversationRepository,
    EventFilter,
    EventRepository,
    MediaRepository,
    MessageFilter,
    MessageRepository,
)
from whatsloon.persistence.models import (
    Conversation,
    Direction,
    MediaMetadata,
    Message,
    MessageStatus,
    ProcessingStatus,
    WebhookEvent,
    utcnow,
)
from whatsloon.persistence.policies import RetentionPolicy, fingerprint
from whatsloon.persistence.repositories import (
    InMemoryConversationRepository,
    InMemoryEventRepository,
    InMemoryMediaRepository,
    InMemoryMessageRepository,
)

__all__ = [
    "Conversation",
    "ConversationRepository",
    "Direction",
    "EventFilter",
    "EventRepository",
    "InMemoryConversationRepository",
    "InMemoryEventRepository",
    "InMemoryMediaRepository",
    "InMemoryMessageRepository",
    "MediaMetadata",
    "MediaRepository",
    "Message",
    "MessageFilter",
    "MessageRepository",
    "MessageStatus",
    "ProcessingStatus",
    "RetentionPolicy",
    "WebhookEvent",
    "fingerprint",
    "utcnow",
]
