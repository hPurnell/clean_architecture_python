"""The Argon2 adapter, on its own.

The costs are turned right down here: these tests are about what the adapter
does with the library's answers, not about how long a real login should take.
"""

import pytest
from argon2 import PasswordHasher

from app.auth.service.argon2_password_service import Argon2PasswordService

PASSWORD = "correct horse battery staple"


def cheap_password_service(**parameters) -> Argon2PasswordService:
    return Argon2PasswordService(
        PasswordHasher(
            **{"time_cost": 1, "memory_cost": 8, "parallelism": 1, **parameters}
        )
    )


@pytest.fixture
def password_service() -> Argon2PasswordService:
    return cheap_password_service()


@pytest.mark.unit
class TestArgon2PasswordService:
    def test_the_password_is_not_in_the_hash(
        self, password_service: Argon2PasswordService
    ):
        password_hash = password_service.hash(PASSWORD)

        assert PASSWORD not in password_hash
        assert password_hash.startswith("$argon2id$")

    def test_verify_accepts_the_password(self, password_service: Argon2PasswordService):
        assert password_service.verify(PASSWORD, password_service.hash(PASSWORD))

    def test_verify_rejects_another_password(
        self, password_service: Argon2PasswordService
    ):
        assert not password_service.verify("wrong", password_service.hash(PASSWORD))

    def test_the_same_password_hashes_differently_every_time(
        self, password_service: Argon2PasswordService
    ):
        # Each hash carries its own salt, so equal passwords do not give
        # themselves away by having equal hashes.
        first = password_service.hash(PASSWORD)
        second = password_service.hash(PASSWORD)

        assert first != second
        assert password_service.verify(PASSWORD, second)

    def test_a_hash_is_verified_with_the_parameters_it_was_made_with(self):
        # Raising the cost must not invalidate the hashes already stored.
        password_hash = cheap_password_service().hash(PASSWORD)

        assert cheap_password_service(time_cost=3, memory_cost=64).verify(
            PASSWORD, password_hash
        )

    @pytest.mark.parametrize(
        "password_hash",
        [
            "",
            "password",
            "$argon2id$v=19$m=8,t=1,p=1$truncated",
            "$scrypt$16384$8$1$0011$0011",
        ],
    )
    def test_verify_rejects_a_hash_it_cannot_read(
        self, password_service: Argon2PasswordService, password_hash: str
    ):
        assert not password_service.verify(PASSWORD, password_hash)
