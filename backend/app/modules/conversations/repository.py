import uuid

from app.models.conversation import Conversation
from app.modules.conversations.schemas import ConversationCreate
from app.utils.text import limit_to_words
from sqlmodel import Session


class ConversationsRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def create(self, conversation_data: ConversationCreate):
        user_id = uuid.UUID(
            "12345678-1234-4234-8234-123456789abc"
        )  # Generate a new UUID for the user
        conversation = Conversation(
            title=limit_to_words(conversation_data.message, 5),
            user_id=user_id,
            last_message_id=None,
            is_pinned=False,
        )

        # Implementation for saving a conversation
        self.session.add(conversation)

        self.session.commit()

        self.session.refresh(conversation)

        return conversation

    def get_by_id(self, conversation_id: uuid.UUID):
        # Implementation for retrieving a conversation by ID
        return self.session.get(Conversation, conversation_id)


class MessagesRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def create(self, message_data):
        # Implementation for saving a message
        self.session.add(message_data)
        self.session.commit()
        self.session.refresh(message_data)
        return message_data

    def update(self, message_data):
        # Implementation for updating a message
        self.session.add(message_data)
        self.session.commit()
        self.session.refresh(message_data)
        return message_data
