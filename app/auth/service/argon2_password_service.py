from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.auth.domain.abstract_password_service import AbstractPasswordService


class Argon2PasswordService(AbstractPasswordService):
    def __init__(self, password_hasher: PasswordHasher | None = None) -> None:
        # The library's defaults are the RFC 9106 profile: Argon2id, 64 MiB,
        # three passes, a few tens of milliseconds per login. Redeclaring them
        # here would only be a second place to get them wrong.
        self._password_hasher = password_hasher or PasswordHasher()

    def hash(self, password: str) -> str:
        return self._password_hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._password_hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            # The wrong password, or a hash this library cannot read. A
            # HashingError is deliberately not caught: failing to hash at all
            # is a broken installation, not a failed login.
            return False
