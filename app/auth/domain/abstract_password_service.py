from abc import ABC, abstractmethod


class AbstractPasswordService(ABC):
    """Port for hashing and checking passwords."""

    @abstractmethod
    def hash(self, password: str) -> str:
        """Return a hash of ``password``, salted per call.

        The salt and the parameters used are part of the returned string, so a
        hash is checked with ``verify`` rather than compared.
        """

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        """Return whether ``password`` produced ``password_hash``.

        A hash this service can no longer read is a failed login, not an error.
        """

    @abstractmethod
    def dummy_verify(self, password: str) -> bool:
        """Do the work of a verify against no real hash, and return False.

        A login for a username that does not exist has to cost what a real one
        costs. Returning early instead lets a caller time the difference and
        learn which usernames are registered.
        """
