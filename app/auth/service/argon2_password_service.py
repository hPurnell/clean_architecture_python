import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.auth.domain.abstract_password_service import AbstractPasswordService


class Argon2PasswordService(AbstractPasswordService):
    def __init__(self, password_hasher: PasswordHasher | None = None) -> None:
        # The library's defaults are the RFC 9106 profile; redeclaring them
        # here would only be a second place to get them wrong.
        self._password_hasher = password_hasher or PasswordHasher()
        # Hashed once, at application scope, so a login for an unknown user can
        # be charged the same work as a real one without paying for it here.
        self._dummy_hash = self._password_hasher.hash(secrets.token_urlsafe(32))

    def hash(self, password: str) -> str:
        return self._password_hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return self._password_hasher.verify(password_hash, password)
        except (VerificationError, InvalidHashError):
            # HashingError is deliberately not caught: failing to hash at all is
            # a broken installation, not a failed login.
            return False

    def dummy_verify(self, password: str) -> bool:
        return self.verify(password, self._dummy_hash)
