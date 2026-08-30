from sqlmodel import Session, select

from app.models.todo import Todo


class TodoRepository:
    def __init__(
        self,
        session: Session,
    ):
        self.session = session

    def create(
        self,
        todo: Todo,
    ) -> Todo:

        self.session.add(todo)

        self.session.commit()

        self.session.refresh(todo)

        return todo

    def get_all(self) -> list[Todo]:

        statement = select(Todo)

        return list(self.session.exec(statement))

    def get_by_id(
        self,
        todo_id: int,
    ) -> Todo | None:

        return self.session.get(
            Todo,
            todo_id,
        )

    def update(
        self,
        todo: Todo,
    ) -> Todo:

        self.session.add(todo)

        self.session.commit()

        self.session.refresh(todo)

        return todo

    def delete(
        self,
        todo: Todo,
    ) -> None:

        self.session.delete(todo)

        self.session.commit()
