import uuid

from sqlmodel import Field, SQLModel

class Todo(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, index=True, nullable=False)
    title: str
    description: str | None = None
    completed: bool = False