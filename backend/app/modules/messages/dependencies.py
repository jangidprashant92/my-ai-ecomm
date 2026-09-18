from typing import Annotated

from app.ai.graph.dependencies import ChatGraphDep
from app.dependencies.database import SessionDep
from app.modules.conversations.dependencies import (
    ConversationsRepositoryDep,
    ConversationsServiceDep,
)
from app.modules.messages.repository import MessagesRepository
from app.modules.messages.services import MessagesService
from fastapi import Depends


def get_messages_repository(
    session: SessionDep,
) -> MessagesRepository:
    return MessagesRepository(
        session=session,
    )


MessagesRepositoryDep = Annotated[
    MessagesRepository,
    Depends(get_messages_repository),
]


def get_messages_service(
    conversation_repository: ConversationsRepositoryDep,
    message_repository: MessagesRepositoryDep,
    conversation_service: ConversationsServiceDep,
    chat_graph: ChatGraphDep,
) -> MessagesService:
    return MessagesService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        conversation_service=conversation_service,
        chat_graph=chat_graph,
    )


MessagesServiceDep = Annotated[
    MessagesService,
    Depends(get_messages_service),
]
