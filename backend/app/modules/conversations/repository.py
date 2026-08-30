from app.modules.conversations.schemas import ConversationCreate
from sqlmodel import Session


class ConversationsRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def create(self, conversation_data: ConversationCreate):
        # Implementation for saving a conversation
        pass
