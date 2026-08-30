from app.modules.conversations.repository import ConversationsRepository
from app.modules.conversations.schemas import ConversationCreate


class ConversationsService:
    def __init__(self, repository: ConversationsRepository):
        self.repository = repository

    def create(self, conversation_data: ConversationCreate):
        # Implementation for creating a conversation
        return self.repository.create(conversation_data)
