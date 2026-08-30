from typing import cast

from fastapi import FastAPI
from starlette.types import ExceptionHandler

from app.common.exception_handlers import (
    app_exception_handler,
    generic_exception_handler,
)
from app.core.exceptions import AppException
from app.modules.todo.routes import router as todo_router

app = FastAPI(title="AI Commerce Platform")

app.add_exception_handler(
    AppException,
    cast(ExceptionHandler, app_exception_handler),
)

app.add_exception_handler(
    Exception,
    generic_exception_handler,
)

app.include_router(todo_router)  # Include the todo router


@app.get("/")
async def root():
    return {"message": "AI Commerce Platform API"}
