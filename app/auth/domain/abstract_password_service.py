from abc import ABC, abstractmethod


class AbstractPasswordService(ABC):
    """
    Port for storing passwords as something other than the password.
    """

    @abstractmethod
    def hash(self, password: str) -> str:
        """Return a self-describing hash that ``verify`` can check later.

        Two calls with the same password return different hashes: the salt is
        generated per call and travels inside the result.
        """

    @abstractmethod
    def verify(self, password: str, password_hash: str) -> bool:
        """Return whether ``password`` is the one ``password_hash`` was made from.

        A hash this implementation cannot read is not a match, and not an
        error: stored hashes outlive the parameters they were made with.
        """
