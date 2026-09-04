import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Text, Uuid
from sqlmodel import Field, SQLModel


# For Memory Type 2: Rolling Conversation Summary
class ConversationSummaryMemory(SQLModel, table=True):
    """Memory for storing rolling conversation summaries."""

    __tablename__ = "conversation_summary_memories"  # type: ignore

    conversation_id: uuid.UUID = Field(
        sa_column=Column(
            Uuid,
            ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
            primary_key=True,
        )
    )
    summary: str = Field(default="", sa_column=Column(Text, nullable=False))
    last_summarized_message_id: uuid.UUID | None = Field(default=None)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )


# For Memory Type 4: Structured Profile / Entity Facts
class UserMemory(SQLModel, table=True):
    """Memory for storing structured user profile or entity facts."""

    __tablename__ = "user_memories"  # type: ignore

    memory_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(index=True, nullable=False)
    category: str = Field(
        index=True, max_length=50
    )  # e.g., "preference", "fact", "skill"
    key: str = Field(max_length=100)  # e.g., "preferred_language"
    value: str = Field(
        sa_column=Column(Text, nullable=False)
    )  # e.g., "TypeScript and Python"
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
