from enum import Enum
from typing import Any

from pydantic import BaseModel


class ChatEventType(str, Enum):
    MESSAGE_START = "message_start"
    TOKEN = "token"
    COMPLETE = "complete"
    ERROR = "error"


class ChatEvent(BaseModel):
    event: ChatEventType
    data: dict[str, Any]
