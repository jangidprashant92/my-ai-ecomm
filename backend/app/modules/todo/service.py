from app.core.exceptions import NotFoundException
from app.models.todo import Todo
from app.modules.todo.repository import TodoRepository
from app.modules.todo.schemas import TodoCreate


class TodoService:
    def __init__(
        self,
        repository: TodoRepository,
    ):
        self.repository = repository

    def create(
        self,
        todo: TodoCreate,
    ) -> Todo:

        new_todo = Todo.model_validate(todo)

        return self.repository.create(new_todo)

    def get_all(
        self,
    ) -> list[Todo]:

        return self.repository.get_all()

    def get_by_id(
        self,
        todo_id: int,
    ) -> Todo:

        todo = self.repository.get_by_id(todo_id)

        if not todo:
            raise NotFoundException(message="Todo not found")

        return todo

    def update(
        self,
        todo_id: int,
        updated_data: dict,
    ) -> Todo:

        todo = self.get_by_id(todo_id)

        for key, value in updated_data.items():
            setattr(
                todo,
                key,
                value,
            )

        return self.repository.update(todo)

    def delete(
        self,
        todo_id: int,
    ) -> None:

        todo = self.get_by_id(todo_id)

        self.repository.delete(todo)
