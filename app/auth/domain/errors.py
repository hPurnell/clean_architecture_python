from app.shared.domain.errors import (
    AuthenticationError,
    ConflictError,
    ValidationError,
)


class InvalidCredentialsError(AuthenticationError):
    def __init__(self) -> None:
        super().__init__("Invalid username or password")


class InvalidTokenError(AuthenticationError):
    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message)


class UsernameTakenError(ConflictError):
    def __init__(self, username: str) -> None:
        super().__init__(f"That username is already registered: {username}")
        self.username = username


class WeakPasswordError(ValidationError):
    def __init__(self, minimum_length: int) -> None:
        super().__init__(
            f"A password must be at least {minimum_length} characters long."
        )
        self.minimum_length = minimum_length
