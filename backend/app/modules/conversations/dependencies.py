from typing import Annotated

from app.dependencies.database import SessionDep
from app.modules.conversations.controller import ConversationsController
from app.modules.conversations.repository import (
    ConversationsRepository,
    MessagesRepository,
)
from app.modules.conversations.services.conversation_service import ConversationsService
from fastapi import Depends


def get_conversation_repository(
    session: SessionDep,
) -> ConversationsRepository:

    return ConversationsRepository(
        session=session,
    )


ConversationsRepositoryDep = Annotated[
    ConversationsRepository,
    Depends(get_conversation_repository),
]


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


def get_conversation_service(
    repository: ConversationsRepositoryDep,
    message_repository: MessagesRepositoryDep,
) -> ConversationsService:

    return ConversationsService(
        repository=repository, message_repository=message_repository
    )


ConversationsServiceDep = Annotated[
    ConversationsService,
    Depends(get_conversation_service),
]


def get_conversation_controller(
    service: ConversationsServiceDep,
) -> ConversationsController:

    return ConversationsController(
        service=service,
    )


ConversationsControllerDep = Annotated[
    ConversationsController,
    Depends(get_conversation_controller),
]
