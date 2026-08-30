from sqlmodel import SQLModel


class ConversationCreate(SQLModel):
    title: str
    description: str | None = None
