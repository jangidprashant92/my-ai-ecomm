from fastapi import APIRouter

from app.modules.todo.dependencies import (
    TodoControllerDep,
)
from app.modules.todo.schemas import (
    TodoCreate,
    TodoUpdate,
)

router = APIRouter(
    prefix="/todos",
    tags=["todos"],
)


@router.get("/")
def get_all_todos(
    controller: TodoControllerDep,
):
    return controller.get_all_todos()


@router.post("/")
def create_todo(
    todo: TodoCreate,
    controller: TodoControllerDep,
):
    return controller.create_todo(todo)


@router.get("/{todo_id}")
def get_todo_by_id(
    todo_id: int,
    controller: TodoControllerDep,
):
    return controller.get_todo_by_id(todo_id)


@router.put("/{todo_id}")
def update_todo(
    todo_id: int,
    todo: TodoUpdate,
    controller: TodoControllerDep,
):
    return controller.update_todo(
        todo_id=todo_id,
        todo_data=todo.model_dump(exclude_unset=True),
    )


@router.delete("/{todo_id}")
def delete_todo(
    todo_id: int,
    controller: TodoControllerDep,
):
    return controller.delete_todo(todo_id)
