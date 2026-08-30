from typing import Any

from fastapi.encoders import jsonable_encoder


class ApiResponse:
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
    ) -> dict:
        return {
            "error": False,
            "errors": [],
            "message": message,
            "data": jsonable_encoder(data) or {},
        }

    @staticmethod
    def fail(
        message: str = "Something went wrong",
        errors: list | dict | None = None,
    ) -> dict:
        return {
            "error": True,
            "errors": errors or [],
            "message": message,
            "data": {},
        }
