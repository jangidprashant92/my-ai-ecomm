import uuid

from app.models.conversation import Conversation
from app.modules.conversations.repository import ConversationsRepository


class ConversationsService:
    """Service for managing conversations."""

    def __init__(
        self,
        repository: ConversationsRepository,
    ):
        self.repository = repository

    async def get_or_create_conversation(
        self,
        conversation_id: uuid.UUID | None,
        title: str,
        user_id: uuid.UUID,
    ) -> Conversation:
        """Return an existing conversation or create a new one."""

        if conversation_id is not None:
            existing = self.repository.get_by_id(conversation_id)

            if existing is not None:
                return existing

        conversation = Conversation(
            user_id=user_id,
            title=title,
        )

        return self.repository.create(conversation)

    def get_conversations_by_user(
        self,
        user_id: uuid.UUID,
        limit: int = 10,
        offset: int = 0,
    ):
        return self.repository.get_by_user_id(
            user_id,
            limit,
            offset,
        )
