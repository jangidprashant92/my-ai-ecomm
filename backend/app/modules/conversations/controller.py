from app.common.base_controller import BaseController
from app.modules.conversations.schemas import ConversationCreate

from .service import ConversationsService


class ConversationsController(BaseController):
    def __init__(
        self,
        service: ConversationsService,
    ):
        self.service = service

    def create_conversation(
        self,
        conversation_data: ConversationCreate,
    ):

        new_conversation = self.service.create(conversation_data)

        return self.success(
            data=new_conversation,
            message="Conversation created successfully",
        )
