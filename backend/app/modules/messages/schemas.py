from enum import Enum
from typing import Any

from pydantic import BaseModel


class ChatEventType(str, Enum):
    MESSAGE_START = "message_start"
    THINKING = "thinking"
    TOKEN = "token"
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
    decision: HumanDecision
    message: str | None = None
