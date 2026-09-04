from dataclasses import replace
from uuid import uuid4

from app.auth.domain.abstract_auth_service import AbstractAuthService
from app.auth.domain.abstract_password_service import AbstractPasswordService
from app.auth.domain.abstract_token_service import AbstractTokenService
from app.auth.domain.abstract_user_repository import AbstractUserRepository
from app.auth.domain.errors import (
    InvalidCredentialsError,
    UsernameTakenError,
    WeakPasswordError,
)
from app.auth.domain.role import Role
from app.auth.domain.token import Token
from app.auth.domain.user import User, normalise_username
from app.shared.clock import utc_now
from app.shared.domain.unit_of_work import AbstractUnitOfWork

MINIMUM_PASSWORD_LENGTH = 12


class AuthService(AbstractAuthService):
    def __init__(
        self,
        unit_of_work: AbstractUnitOfWork,
        token_service: AbstractTokenService,
        password_service: AbstractPasswordService,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._token_service = token_service
        self._password_service = password_service

    @property
    def _users(self) -> AbstractUserRepository:
        return self._unit_of_work.repository(AbstractUserRepository)

    def register(self, name: str, username: str, password: str) -> User:
        username = normalise_username(username)
        if len(password) < MINIMUM_PASSWORD_LENGTH:
            raise WeakPasswordError(MINIMUM_PASSWORD_LENGTH)
        if self._users.get_user(username) is not None:
            raise UsernameTakenError(username)

        now = utc_now()
        user = self._users.add(
            User(
                id=uuid4().hex,
                name=name,
                username=username,
                password_hash=self._password_service.hash(password),
                # Nobody registers themselves an administrator; that is granted
                # out of band.
                roles=frozenset({Role.USER}),
                created_date=now,
                modified_date=now,
            )
        )
        self._unit_of_work.commit()
        return user

    def login(self, username: str, password: str) -> str:
        user = self._users.get_user(normalise_username(username))
        if user is None:
            # Charged the same work as a real check, so the time taken does not
            # say whether this username is registered.
            self._password_service.dummy_verify(password)
            raise InvalidCredentialsError()

        if not self._password_service.verify(password, user.password_hash):
            raise InvalidCredentialsError()

        return self._token_service.encode(user.username, user.roles)

    def change_password(
        self, username: str, current_password: str, new_password: str
    ) -> None:
        user = self._users.get_user(normalise_username(username))
        if user is None or not self._password_service.verify(
            current_password, user.password_hash
        ):
            raise InvalidCredentialsError()
        if len(new_password) < MINIMUM_PASSWORD_LENGTH:
            raise WeakPasswordError(MINIMUM_PASSWORD_LENGTH)

        self._users.update(
            replace(
                user,
                password_hash=self._password_service.hash(new_password),
                modified_date=utc_now(),
            )
        )
        self._unit_of_work.commit()

    def verify(self, encoded_token: str) -> Token:
        return self._token_service.decode(encoded_token)
