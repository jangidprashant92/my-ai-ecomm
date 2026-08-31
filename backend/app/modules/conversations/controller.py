from app.common.base_controller import BaseController
from app.modules.conversations.schemas import ConversationCreate
from fastapi.responses import StreamingResponse

from .services.conversation_service import ConversationsService


class ConversationsController(BaseController):
    def __init__(
        self,
        service: ConversationsService,
    ):
        self.service = service

    async def create_conversation(
        self,
        conversation_data: ConversationCreate,
    ):

        new_conversation = self.service.send_message(conversation_data)

        # return self.success(
        #     data=new_conversation,
        #     message="Conversation created successfully",
        # )

        return StreamingResponse(
            new_conversation,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
