import uuid

from app.models.conversation import Conversation
from app.modules.conversations.repository import (
    ConversationsRepository,
)


class ConversationsService:
    """Service for managing conversations."""

    def __init__(
        self,
        repository: ConversationsRepository,
    ):
        self.repository = repository

    async def get_or_create_conversation(
        self, conversation_data: Conversation
    ) -> Conversation:
        """Get an existing conversation by ID or create a new one if it doesn't exist."""

        # Check if a conversation with the same title exists
        if conversation_data.conversation_id:
            exiting = self.repository.get_by_id(conversation_data.conversation_id)
            if exiting:
                return exiting

        del (
            conversation_data.conversation_id
        )  # Remove the ID to ensure a new conversation is created
        return self.repository.create(conversation_data)

    def get_conversations_by_user(
        self, user_id: uuid.UUID, limit: int = 10, offset: int = 0
    ):
        """Get all conversations for a specific user."""
        return self.repository.get_by_user_id(user_id, limit, offset)
