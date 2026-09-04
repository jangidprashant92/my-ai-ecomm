from app.common.api_response import ApiResponse
from app.core.exceptions import AppException
from fastapi import Request
from fastapi.responses import JSONResponse


async def app_exception_handler(
    request: Request,
    exc: AppException,
):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse.fail(
            message=exc.message,
            errors=exc.errors,
        ),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
):
    # Log exc here

    return JSONResponse(
        status_code=500,
        content=ApiResponse.fail(
            message="Internal server error",
        ),
    )
