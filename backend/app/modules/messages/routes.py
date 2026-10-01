import uuid

from app.common.base_controller import BaseController
from app.modules.conversations.schemas import ConversationCreate
from app.modules.messages.dependencies import MessagesServiceDep
from app.modules.messages.schemas import HumanReviewRequest
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)


@router.post("/send-message")
async def send_message(
    conversation: ConversationCreate,
    service: MessagesServiceDep,
):
    new_conversation = service.send_message(conversation)

    return StreamingResponse(
        new_conversation,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/get-messages/{conversation_id}")
async def get_messages(
    conversation_id: uuid.UUID,
    service: MessagesServiceDep,
):
    """Get all messages for a specific conversation."""
    messages = service.get_messages_by_conversation(conversation_id)

    return BaseController().success(
        data={"messages": messages},
    )


@router.post(
    "/conversations/{conversation_id}/human-review",
)
async def human_review(
    conversation_id: uuid.UUID,
    review: HumanReviewRequest,
    service: MessagesServiceDep,
):
    return StreamingResponse(
        service.resume_human_review(
            conversation_id=conversation_id,
            review=review,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
