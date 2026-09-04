from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.auth.domain.abstract_password_service import AbstractPasswordService


class Argon2PasswordService(AbstractPasswordService):
    def __init__(self, password_hasher: PasswordHasher | None = None) -> None:
        # The library's defaults are the RFC 9106 profile; redeclaring them
        # here would only be a second place to get them wrong.
        self._password_hasher = password_hasher or PasswordHasher()

    def hash(self, password: str) -> str:
        return self._password_hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._password_hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            # HashingError is deliberately not caught: failing to hash at all is
            # a broken installation, not a failed login.
            return False
