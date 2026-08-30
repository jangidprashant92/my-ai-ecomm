from app.common.base_controller import BaseController
from app.modules.todo.schemas import TodoCreate
from app.modules.todo.service import TodoService


class TodoController(BaseController):
    def __init__(
        self,
        service: TodoService,
    ):
        self.service = service

    def create_todo(
        self,
        todo: TodoCreate,
    ):

        new_todo = self.service.create(todo)

        return self.success(
            data=new_todo,
            message="Todo created successfully",
        )

    def get_all_todos(self):

        todos = self.service.get_all()

        return self.success(
            data=todos,
            message="Todos fetched successfully",
        )

    def get_todo_by_id(
        self,
        todo_id: int,
    ):

        todo = self.service.get_by_id(todo_id)

        return self.success(
            data=todo,
            message="Todo fetched successfully",
        )

    def update_todo(
        self,
        todo_id: int,
        todo_data: dict,
    ):

        todo = self.service.update(
            todo_id=todo_id,
            updated_data=todo_data,
        )

        return self.success(
            data=todo,
            message="Todo updated successfully",
        )

    def delete_todo(
        self,
        todo_id: int,
    ):

        self.service.delete(todo_id)

        return self.success(
            data=None,
            message="Todo deleted successfully",
        )
