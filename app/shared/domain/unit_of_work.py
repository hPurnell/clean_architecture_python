"""The application-wide unit of work port.

A unit of work is a transaction boundary for the *whole* application, not for a
single aggregate, so this abstraction knows nothing about items, users, or any
other aggregate. Concrete implementations are given the repositories they
should expose at construction time, and callers look one up by its port type::

    items = unit_of_work.repository(AbstractItemRepository)

Adding a new aggregate therefore means registering one more repository in the
composition root, with no change to this class or to any existing aggregate.
"""

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Optional, Type, TypeVar

TRepository = TypeVar("TRepository")


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
