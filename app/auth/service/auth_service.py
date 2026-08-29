from app.auth.domain.abstract_password_service import AbstractPasswordService
from app.auth.domain.abstract_token_service import AbstractTokenService
from app.auth.domain.abstract_user_respository import AbstractUserRepository
from app.auth.domain.errors import InvalidCredentialsError
from app.auth.domain.token import Token


class AuthService:
    def __init__(
        self,
        user_repository: AbstractUserRepository,
        token_service: AbstractTokenService,
        password_service: AbstractPasswordService,
    ) -> None:
        self._user_repository = user_repository
        self._token_service = token_service
        self._password_service = password_service

    def login(self, username: str, password: str) -> str:
        user = self._user_repository.get_user(username.lower())
        if user is None:
            raise InvalidCredentialsError()

        if not self._password_service.verify(password, user.password_hash):
            raise InvalidCredentialsError()

        return self._token_service.encode(user.username)

    def verify(self, encoded_token: str) -> Token:
        return self._token_service.decode(encoded_token)
