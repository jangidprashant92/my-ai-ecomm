from pathlib import Path
from typing import cast

from app.common.exception_handlers import (
    app_exception_handler,
    generic_exception_handler,
)
from app.core.exceptions import AppException
from app.core.lifespan import lifespan
from app.modules.conversations.routes import router as conversations_router
from app.modules.messages.routes import router as messages_router
from app.modules.todo.routes import router as todo_router
from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)
from starlette.types import ExceptionHandler

# # Configure MLflow Tracking URI (Local or Remote)
# mlflow.set_tracking_uri("http://127.0.0.1:8080")
# mlflow.set_experiment("Chat Bot")
# mlflow.autolog()

app = FastAPI(title="AI Commerce Platform", lifespan=lifespan)

PROJECT_ROOT = Path(__file__).resolve().parent

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
app.include_router(messages_router)  # Include the messages router


@app.get("/")
async def root():
    return {"message": "AI Commerce Platform API"}
