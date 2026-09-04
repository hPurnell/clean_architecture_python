from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type, TypeVar

TRepository = TypeVar("TRepository")


# A transaction boundary for the application rather than for one aggregate,
# so callers look a repository up by its port type.
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
        """Return the repository registered for ``port``, or raise KeyError."""
