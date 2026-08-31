import uuid

from sqlmodel import SQLModel


class ConversationCreate(SQLModel):
    conversation_id: uuid.UUID | None = None
    message: str
