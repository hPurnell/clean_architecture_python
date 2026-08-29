from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type, TypeVar

TRepository = TypeVar("TRepository")


# A transaction boundary for the whole application rather than for one
# aggregate, so this port names no aggregate: implementations are handed the
# repositories they expose, and callers look one up by its port type. Adding an
# aggregate means registering a repository in the composition root, nothing here.
class AbstractUnitOfWork(ABC):
    @abstractmethod
    def __enter__(self) -> "AbstractUnitOfWork": ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None: ...

    @abstractmethod
    def commit(self) -> None: ...

    @abstractmethod
    def rollback(self) -> None: ...

    @abstractmethod
    def repository(self, port: Type[TRepository]) -> TRepository:
        """Return the repository registered for ``port``.

        Raises:
            KeyError: if no repository was registered for that port.
        """
