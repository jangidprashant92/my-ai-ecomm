from typing import cast

from app.common.exception_handlers import (
    app_exception_handler,
    generic_exception_handler,
)
from app.core.exceptions import AppException
from app.modules.conversations.routes import router as conversations_router
from app.modules.todo.routes import router as todo_router
from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from starlette.types import ExceptionHandler

app = FastAPI(title="AI Commerce Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(
    AppException,
    cast(ExceptionHandler, app_exception_handler),
)

app.add_exception_handler(
    Exception,
    generic_exception_handler,
)

app.include_router(todo_router)  # Include the todo router
app.include_router(conversations_router)  # Include the conversations router


@app.get("/")
async def root():
    return {"message": "AI Commerce Platform API"}
