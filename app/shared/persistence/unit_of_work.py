from types import TracebackType
from typing import Any, Callable, Mapping, Optional, Type, TypeVar, cast

from sqlalchemy.orm import Session, sessionmaker

from app.shared.domain.unit_of_work import AbstractUnitOfWork

TRepository = TypeVar("TRepository")

# Bound to the active session, so every repository shares one transaction.
RepositoryFactory = Callable[[Session], Any]


class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        session_factory: sessionmaker[Session],
        repository_factories: Mapping[Type[Any], RepositoryFactory],
    ) -> None:
        self._session_factory = session_factory
        self._repository_factories = dict(repository_factories)
        self._session: Optional[Session] = None
        self._repositories: dict[Type[Any], Any] = {}

    def __enter__(self) -> "SqlAlchemyUnitOfWork":
        self._session = self._session_factory()
        self._repositories = {
            port: factory(self._session)
            for port, factory in self._repository_factories.items()
        }
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        # Anything not explicitly committed is discarded.
        self.rollback()
        if self._session is not None:
            self._session.close()
        self._session = None
        self._repositories = {}

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError(
                "Unit of work used outside of its context manager. "
                "Enter it with 'with unit_of_work: ...' first."
            )
        return self._session

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        if self._session is not None:
            self._session.rollback()

    def repository(self, port: Type[TRepository]) -> TRepository:
        try:
            return cast(TRepository, self._repositories[port])
        except KeyError:
            raise KeyError(
                f"No repository registered for {port.__name__}. "
                "Register one in the composition root's repository factories."
            ) from None
