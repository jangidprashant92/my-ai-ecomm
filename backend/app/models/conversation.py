import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Uuid
from sqlmodel import Field, Relationship, SQLModel


class Conversation(SQLModel, table=True):
    conversation_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(nullable=False, index=True)
    title: str = Field(default="New Chat", max_length=255)
    is_pinned: bool = Field(default=False, nullable=False)

    # The crucial pointer tracking the current active leaf node of the chat tree
    last_message_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            Uuid,
            ForeignKey(
                "messages.message_id",
                name="fk_conversations_last_message_id_messages",
                ondelete="SET NULL",
                use_alter=True,
            ),
            nullable=True,
        ),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    # user: User = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"foreign_keys": "Message.conversation_id"},
    )


class Message(SQLModel, table=True):
    message_id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    conversation_id: uuid.UUID = Field(
        foreign_key="conversation.conversation_id", ondelete="CASCADE", nullable=False
    )

    # Self-referencing link to construct branching chat histories
    parent_message_id: uuid.UUID | None = Field(
        default=None, foreign_key="message.message_id", ondelete="SET NULL"
    )

    role: str = Field(nullable=False, max_length=20)  # 'system', 'user', or 'assistant'
    content: str = Field(nullable=False)

    # Version metadata
    version: int = Field(default=1, nullable=False)
    is_edited: bool = Field(default=False, nullable=False)

    # Performance & billing tracing
    prompt_tokens: int = Field(default=0)
    completion_tokens: int = Field(default=0)

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    conversation: Conversation = Relationship(
        back_populates="messages",
        sa_relationship_kwargs={"foreign_keys": "[Message.conversation_id]"},
    )
