from typing import Annotated

from app.dependencies.database import SessionDep
from app.modules.conversations.repository import (
    ConversationsRepository,
)
from app.modules.conversations.services import ConversationsService
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


def get_conversation_service(
    repository: ConversationsRepositoryDep,
) -> ConversationsService:

    return ConversationsService(
        repository=repository,
    )


ConversationsServiceDep = Annotated[
    ConversationsService,
    Depends(get_conversation_service),
]
