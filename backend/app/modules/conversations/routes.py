from app.modules.conversations.dependencies import ConversationsControllerDep
from app.modules.conversations.schemas import ConversationCreate
from fastapi import APIRouter

router = APIRouter(
    prefix="/conversations",
    tags=["conversations"],
)


@router.post("/")
def create_conversation(
    conversation: ConversationCreate,
    controller: ConversationsControllerDep,
):
    return controller.create_conversation(conversation)
