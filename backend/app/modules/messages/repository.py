import uuid
from collections.abc import Sequence

from app.models.conversation import Message
from app.shared.repository import BaseRepository
from sqlmodel import Session, asc, desc, select


class MessagesRepository(BaseRepository[Message]):
    def __init__(
        self,
        session: Session,
    ):
        super().__init__(session, model=Message)

    def get_messages_by_conversation(self, conversation_id: str):
        """Get all messages for a specific conversation."""
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(asc(Message.created_at))
        )
        return self.session.exec(statement).all()

    async def get_last_messages(
        self, conversation_id: uuid.UUID, limit: int = 5
    ) -> list[Message]:
        """Get the last N messages for a specific conversation."""
        statement = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            # Sort descending to grab the most recent N records
            .order_by(desc(Message.created_at))
            .limit(limit)
        )
        recent_messages: Sequence[Message] = self.session.exec(statement).all()

        # Reverse them so they are returned in chronological order
        return list(reversed(recent_messages))
