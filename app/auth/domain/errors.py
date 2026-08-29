from app.shared.domain.errors import AuthenticationError


class InvalidCredentialsError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Invalid username or password")


class InvalidTokenError(AuthenticationError):
    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message)
