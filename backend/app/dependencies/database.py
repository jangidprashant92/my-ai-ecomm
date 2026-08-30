from typing import Annotated

from app.core.database import get_session
from fastapi import Depends
from sqlmodel import Session

SessionDep = Annotated[
    Session,
    Depends(get_session),
]