from typing import Any

from app.common.api_response import ApiResponse


class BaseController:
    """
    Base controller shared by all API controllers.
    """

    def success(
        self,
        data: Any = None,
        message: str = "",
    ):
        return ApiResponse.success(
            data=data,
            message=message,
        )
