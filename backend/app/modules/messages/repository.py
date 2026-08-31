from app.models.conversation import Message
from app.shared.repository import BaseRepository
from sqlmodel import Session


class MessagesRepository(BaseRepository[Message]):
    def __init__(
        self,
        session: Session,
    ):
        super().__init__(session, model=Message)
