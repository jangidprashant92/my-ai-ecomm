from typing import Annotated

from app.ai.llm.base import BaseLLMProvider
from app.ai.llm.dependencies import get_llm_provider
from app.dependencies.database import SessionDep
from app.modules.conversations.dependencies import (
    ConversationsRepositoryDep,
    ConversationsServiceDep,
)
from app.modules.memory.services import UnifiedMemoryManager
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


LLMProviderDep = Annotated[
    BaseLLMProvider,
    Depends(get_llm_provider),
]


def get_memory_manager(
    session: SessionDep,
    message_repo: MessagesRepositoryDep,
    llm: LLMProviderDep,
) -> UnifiedMemoryManager:

    return UnifiedMemoryManager(
        session=session,
        message_repo=message_repo,
        llm=llm,
    )


MemoryDep = Annotated[
    UnifiedMemoryManager,
    Depends(get_memory_manager),
]


def get_messages_service(
    conversation_repository: ConversationsRepositoryDep,
    message_repository: MessagesRepositoryDep,
    llm: LLMProviderDep,
    conversation_service: ConversationsServiceDep,
    memory_manager: MemoryDep,
) -> MessagesService:

    return MessagesService(
        conversation_repository=conversation_repository,
        message_repository=message_repository,
        llm=llm,
        conversation_service=conversation_service,
        memory_manager=memory_manager,
    )


MessagesServiceDep = Annotated[
    MessagesService,
    Depends(get_messages_service),
]
