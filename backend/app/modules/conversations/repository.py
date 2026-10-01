import uuid

from app.models.conversation import Conversation
from app.shared.repository import BaseRepository
from sqlmodel import Session, desc, select


class ConversationsRepository(BaseRepository[Conversation]):
    """Repository for managing conversations in the database."""

    def __init__(
        self,
        session: Session,
    ):
        super().__init__(session, model=Conversation)

    def get_by_user_id(self, user_id: uuid.UUID, limit: int = 10, offset: int = 0):
        """Get all conversations for a specific user."""
        statement = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .offset(offset)  # Skip the first N items
            .limit(limit)  # Limit the total results returned
        )
        return self.session.exec(statement).all()

    def get(self, conversation_id: uuid.UUID):
        statement = (
            select(Conversation)
            .where(Conversation.conversation_id == conversation_id)
            .order_by(desc(Conversation.updated_at))
        )

        return self.session.exec(statement).first()
