class AppException(Exception):
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        errors: list | dict | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.errors = errors or []


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=404,
        )


class BadRequestException(AppException):
    def __init__(
        self,
        message: str = "Bad request",
        errors=None,
    ):
        super().__init__(
            message=message,
            status_code=400,
            errors=errors,
        )


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=401,
        )