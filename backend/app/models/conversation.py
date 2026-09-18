import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, Column, ForeignKey
from sqlalchemy.types import UUID as NativeUUID
from sqlmodel import Field, Relationship, SQLModel


class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"  # type: ignore
    conversation_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            NativeUUID(as_uuid=True),
            primary_key=True,
            default=uuid.uuid4,
            nullable=False,
        ),
    )
    user_id: uuid.UUID = Field(NativeUUID(as_uuid=True), nullable=False, index=True)
    title: str = Field(default="New Chat", max_length=255)
    is_pinned: bool = Field(default=False, nullable=False)

    last_message_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            NativeUUID(as_uuid=True),
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
        default_factory=lambda: datetime.now(UTC), nullable=False
    )

    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={
            "foreign_keys": "Message.conversation_id",
            "cascade": "all, delete-orphan",
        },
    )


class Message(SQLModel, table=True):
    __tablename__ = "messages"  # type: ignore
    message_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(
            NativeUUID(as_uuid=True),
            primary_key=True,
        ),
    )
    conversation_id: uuid.UUID = Field(
        sa_column=Column(
            NativeUUID(as_uuid=True),
            ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )

    parent_message_id: uuid.UUID | None = Field(
        default=None,
        sa_column=Column(
            NativeUUID(as_uuid=True),
            ForeignKey("messages.message_id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    role: str = Field(nullable=False, max_length=20)  # 'system', 'user', 'assistant'

    # Store multi-modal blocks: text, images, files, or tool outputs
    content: list[dict[str, Any]] = Field(
        sa_column=Column(JSON, nullable=False, default=[])
    )

    # Status tracking (e.g. {"type": "complete", "reason": "stop"} or {"type": "incomplete"})
    status: dict[str, Any] | None = Field(
        default_factory=None, sa_column=Column(JSON, nullable=True)
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), nullable=False
    )

    conversation: Conversation | None = Relationship(
        back_populates="messages",
        sa_relationship_kwargs={"foreign_keys": "Message.conversation_id"},
    )
