import uuid

from app.common.base_controller import BaseController
from app.modules.conversations.dependencies import ConversationsServiceDep
from fastapi import APIRouter

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.get("/")
async def get_conversations(service: ConversationsServiceDep):
    """Get a list of all conversations."""
    conversations = service.get_conversations_by_user(
        user_id=uuid.UUID("12345678-1234-4234-8234-123456789abc")
    )  # Replace with actual user ID logic

    return BaseController().success(
        data=conversations,
        message="Conversations retrieved successfully.",
    )
