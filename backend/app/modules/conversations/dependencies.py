from typing import Annotated

from app.ai.llm.base import BaseLLMProvider
from app.ai.llm.dependencies import get_llm_provider
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


LLMProviderDep = Annotated[
    BaseLLMProvider,
    Depends(get_llm_provider),
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
