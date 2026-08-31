from app.modules.conversations.schemas import ConversationCreate
from app.modules.messages.dependencies import MessagesServiceDep
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter(
    prefix="/messages",
    tags=["messages"],
)


@router.post("/send-message")
async def send_message(
    conversation: ConversationCreate,
    # controller: ConversationsControllerDep,
    service: MessagesServiceDep,
):
    """Send a message in a conversation and stream the response from the LLM."""

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
