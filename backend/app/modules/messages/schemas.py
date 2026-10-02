import uuid
from enum import Enum
from typing import Any

from pydantic import BaseModel


class ChatEventType(str, Enum):
    MESSAGE_START = "message_start"
    TOKEN = "token"
    THINKING = "thinking"
    SOURCES = "sources"
    INTERRUPT = "interrupt"
    COMPLETE = "complete"
    ERROR = "error"


class ChatEvent(BaseModel):
    event: ChatEventType
    data: dict[str, Any]


class HumanDecision(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


class HumanReviewRequest(BaseModel):
    assistant_message_id: uuid.UUID
    decision: HumanDecision
    message: str | None = None
