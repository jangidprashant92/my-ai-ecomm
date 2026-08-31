from app.modules.conversations.dependencies import ConversationsControllerDep
from app.modules.conversations.schemas import ConversationCreate
from fastapi import APIRouter

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.post("/create")
async def create_conversation(
    conversation: ConversationCreate,
    controller: ConversationsControllerDep,
):
    return await controller.create_conversation(conversation)
