import pytest

from app.auth.db.fake_user_repository import DEFAULT_PASSWORD, FakeUserRepository
from app.auth.domain.abstract_password_service import AbstractPasswordService
from app.auth.domain.abstract_user_repository import AbstractUserRepository
from app.auth.domain.errors import (
    InvalidCredentialsError,
    UsernameTakenError,
    WeakPasswordError,
)
from app.auth.service.argon2_password_service import Argon2PasswordService
from app.auth.service.auth_service import MINIMUM_PASSWORD_LENGTH, AuthService
from app.auth.service.jwt_token_service import JwtTokenService
from app.shared.persistence.in_memory_unit_of_work import InMemoryUnitOfWork


class RecordingPasswordService(AbstractPasswordService):
    """A real Argon2 service that counts which verify path was taken."""

    def __init__(self) -> None:
        self._inner = Argon2PasswordService()
        self.verifications = 0
        self.dummy_verifications = 0

    def hash(self, password: str) -> str:
        return self._inner.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        self.verifications += 1
        return self._inner.verify(password, password_hash)

    def dummy_verify(self, password: str) -> bool:
        self.dummy_verifications += 1
        return self._inner.dummy_verify(password)


SEEDED = "john.doe@example.com"
GOOD_PASSWORD = "a long enough password"


@pytest.fixture
def user_repository() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.fixture
def auth_service(user_repository: FakeUserRepository) -> AuthService:
    return AuthService(
        InMemoryUnitOfWork({AbstractUserRepository: user_repository}),
        JwtTokenService(secret="supersecretkey"),
        Argon2PasswordService(),
    )


@pytest.mark.unit
class TestRegister:
    def test_a_registered_user_can_log_in(self, auth_service: AuthService):
        auth_service.register("Ada", "ada@example.com", GOOD_PASSWORD)

        token = auth_service.login("ada@example.com", GOOD_PASSWORD)

        assert auth_service.verify(token).sub == "ada@example.com"

    def test_the_password_is_never_stored(
        self, auth_service: AuthService, user_repository: FakeUserRepository
    ):
        auth_service.register("Ada", "ada@example.com", GOOD_PASSWORD)

        stored = user_repository.get_user("ada@example.com")
        assert stored is not None
        assert GOOD_PASSWORD not in stored.password_hash

    def test_the_username_is_stored_normalised(self, auth_service: AuthService):
        auth_service.register("Ada", "  Ada@Example.COM ", GOOD_PASSWORD)

        # Registered in one case, logged in with another: the same account.
        assert auth_service.login("ada@example.com", GOOD_PASSWORD)

    def test_a_username_cannot_be_taken_twice(self, auth_service: AuthService):
        auth_service.register("Ada", "ada@example.com", GOOD_PASSWORD)

        with pytest.raises(UsernameTakenError):
            auth_service.register("Someone Else", "ADA@example.com", GOOD_PASSWORD)

    def test_a_short_password_is_refused(self, auth_service: AuthService):
        with pytest.raises(WeakPasswordError):
            auth_service.register(
                "Ada", "ada@example.com", "a" * (MINIMUM_PASSWORD_LENGTH - 1)
            )


@pytest.mark.unit
class TestChangePassword:
    def test_the_new_password_replaces_the_old(self, auth_service: AuthService):
        auth_service.change_password(SEEDED, DEFAULT_PASSWORD, GOOD_PASSWORD)

        assert auth_service.login(SEEDED, GOOD_PASSWORD)
        with pytest.raises(InvalidCredentialsError):
            auth_service.login(SEEDED, DEFAULT_PASSWORD)

    def test_the_current_password_has_to_be_right(self, auth_service: AuthService):
        with pytest.raises(InvalidCredentialsError):
            auth_service.change_password(SEEDED, "not the password", GOOD_PASSWORD)

    def test_an_unknown_user_is_not_distinguishable(self, auth_service: AuthService):
        with pytest.raises(InvalidCredentialsError):
            auth_service.change_password("nobody@example.com", "x", GOOD_PASSWORD)

    def test_the_new_password_must_be_strong_enough(self, auth_service: AuthService):
        with pytest.raises(WeakPasswordError):
            auth_service.change_password(SEEDED, DEFAULT_PASSWORD, "short")


@pytest.mark.unit
class TestLoginDoesNotLeakWhoExists:
    def test_an_unknown_user_is_charged_the_same_work(
        self, user_repository: FakeUserRepository
    ):
        """A wrong password and an unknown username must cost the same.

        Asserted on the call rather than on the clock: wall-clock timing is
        unreliable on a loaded machine, and a test that flakes under
        `pytest -n auto` is worse than no test. Removing the dummy verify
        still fails this, which is what it is guarding.
        """
        password_service = RecordingPasswordService()
        auth_service = AuthService(
            InMemoryUnitOfWork({AbstractUserRepository: user_repository}),
            JwtTokenService(secret="supersecretkey"),
            password_service,
        )

        with pytest.raises(InvalidCredentialsError):
            auth_service.login("nobody@example.com", "not the password")

        assert password_service.dummy_verifications == 1

    def test_a_known_user_with_a_wrong_password_verifies_once(
        self, user_repository: FakeUserRepository
    ):
        password_service = RecordingPasswordService()
        auth_service = AuthService(
            InMemoryUnitOfWork({AbstractUserRepository: user_repository}),
            JwtTokenService(secret="supersecretkey"),
            password_service,
        )

        with pytest.raises(InvalidCredentialsError):
            auth_service.login(SEEDED, "not the password")

        # One real verify and no dummy: the two paths do one hash each.
        assert password_service.verifications == 1
        assert password_service.dummy_verifications == 0
