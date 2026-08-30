from typing import Annotated

from app.dependencies.database import SessionDep
from app.modules.todo.controller import TodoController
from app.modules.todo.repository import TodoRepository
from app.modules.todo.service import TodoService
from fastapi import Depends


def get_todo_repository(
    session: SessionDep,
) -> TodoRepository:

    return TodoRepository(
        session=session,
    )


TodoRepositoryDep = Annotated[
    TodoRepository,
    Depends(get_todo_repository),
]


def get_todo_service(
    repository: TodoRepositoryDep,
) -> TodoService:

    return TodoService(
        repository=repository,
    )


TodoServiceDep = Annotated[
    TodoService,
    Depends(get_todo_service),
]

def get_todo_controller(
    service: TodoServiceDep,
) -> TodoController:

    return TodoController(
        service=service,
    )


TodoControllerDep = Annotated[
    TodoController,
    Depends(get_todo_controller),
]