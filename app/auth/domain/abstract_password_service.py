from abc import ABC, abstractmethod


class AbstractPasswordService(ABC):
    """
    Port for hashing and checking passwords.
    """

    @abstractmethod
    def hash(self, password: str) -> str:
        """Return a hash of ``password``, salted per call.

        The same password hashes differently every time, so hashes must be
        checked with ``verify`` rather than compared. The salt and the
        parameters used are part of the returned string; there is nothing else
        to store alongside it.
        """

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        """Return whether ``password`` produced ``password_hash``.

        Returns ``False``, rather than raising, when the hash cannot be read at
        all: a hash left over from parameters this service no longer supports
        is a failed login, not a broken one.
        """
