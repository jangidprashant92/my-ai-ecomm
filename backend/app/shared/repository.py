from typing import Generic, TypeVar

from sqlmodel import Session, SQLModel

ModelType = TypeVar(
    "ModelType",
    bound=SQLModel,
)


class BaseRepository(Generic[ModelType]):
    def __init__(
        self,
        session: Session,
        model: type[ModelType],
    ):
        self.session = session
        self.model = model

    def get_by_id(
        self,
        id,
    ) -> ModelType | None:

        return self.session.get(
            self.model,
            id,
        )

    def create(
        self,
        obj: ModelType,
    ) -> ModelType:

        self.session.add(obj)

        return obj

    def update(
        self,
        obj: ModelType,
    ) -> ModelType:

        self.session.add(obj)

        return obj

    def delete(
        self,
        obj: ModelType,
    ) -> None:

        self.session.delete(obj)
