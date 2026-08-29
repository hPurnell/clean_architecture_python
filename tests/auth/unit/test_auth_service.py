import pytest

from app.auth.db.fake_user_respository import DEFAULT_PASSWORD, FakeUserRepository
from app.auth.domain.errors import InvalidCredentialsError
from app.auth.service.argon2_password_service import Argon2PasswordService
from app.auth.service.auth_service import AuthService
from app.auth.service.jwt_token_service import JwtTokenService

USERNAME = "john.doe@example.com"


@pytest.fixture
def auth_service() -> AuthService:
    return AuthService(
        FakeUserRepository(),
        JwtTokenService(secret="supersecretkey"),
        Argon2PasswordService(),
    )


@pytest.mark.unit
class TestAuthService:
    def test_the_seeded_user_is_stored_hashed(self):
        user = FakeUserRepository().get_user(USERNAME)

        assert user is not None
        assert user.password_hash != DEFAULT_PASSWORD
        assert DEFAULT_PASSWORD not in user.password_hash

    def test_login_with_the_right_password(self, auth_service: AuthService):
        token = auth_service.login(USERNAME, DEFAULT_PASSWORD)

        assert auth_service.verify(token).sub == USERNAME

    def test_login_with_the_wrong_password(self, auth_service: AuthService):
        with pytest.raises(InvalidCredentialsError):
            auth_service.login(USERNAME, "not the password")

    def test_login_with_the_stored_hash_as_the_password(
        self, auth_service: AuthService
    ):
        # Presenting the stored hash is not presenting the password.
        user = FakeUserRepository().get_user(USERNAME)
        assert user is not None

        with pytest.raises(InvalidCredentialsError):
            auth_service.login(USERNAME, user.password_hash)

    def test_login_with_an_unknown_user(self, auth_service: AuthService):
        with pytest.raises(InvalidCredentialsError):
            auth_service.login("nobody@example.com", DEFAULT_PASSWORD)
