import pytest

from app.auth.db.fake_user_respository import DEFAULT_PASSWORD, FakeUserRepository

USERNAME = "john.doe@example.com"


@pytest.fixture
def repository() -> FakeUserRepository:
    return FakeUserRepository()


@pytest.mark.unit
class TestFakeUserRepository:
    def test_it_returns_the_seeded_user(self, repository: FakeUserRepository):
        user = repository.get_user(USERNAME)

        assert user is not None
        assert user.username == USERNAME

    def test_the_seeded_user_carries_a_hash_not_the_password(
        self, repository: FakeUserRepository
    ):
        user = repository.get_user(USERNAME)

        assert user is not None
        assert user.password_hash != DEFAULT_PASSWORD
        assert DEFAULT_PASSWORD not in user.password_hash
        assert user.password_hash.startswith("$argon2id$")

    def test_it_returns_none_for_an_unknown_user(self, repository: FakeUserRepository):
        assert repository.get_user("nobody@example.com") is None

    def test_lookup_is_case_sensitive(self, repository: FakeUserRepository):
        # Matching is verbatim; AuthService lowercases before it gets here.
        assert repository.get_user(USERNAME.upper()) is None
