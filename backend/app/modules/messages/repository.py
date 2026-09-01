from app.models.conversation import Message
from app.shared.repository import BaseRepository
from sqlmodel import Session, asc, select


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
