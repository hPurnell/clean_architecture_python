from types import TracebackType
from typing import Any, Mapping, Optional, Type, TypeVar, cast

from app.shared.domain.unit_of_work import AbstractUnitOfWork

TRepository = TypeVar("TRepository")


class InMemoryUnitOfWork(AbstractUnitOfWork):
    # Repositories are injected rather than created here, so how long the data
    # survives is a wiring decision: the test container binds them at app scope,
    # giving each test app instance its own isolated store.
    def __init__(self, repositories: Mapping[Type[Any], Any]) -> None:
        self._repositories = dict(repositories)

    def __enter__(self) -> "InMemoryUnitOfWork":
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        return None

    def commit(self) -> None:
        return None

    def rollback(self) -> None:
        return None

    def repository(self, port: Type[TRepository]) -> TRepository:
        try:
            return cast(TRepository, self._repositories[port])
        except KeyError:
            raise KeyError(
                f"No repository registered for {port.__name__}. "
                "Register one in the composition root's repository factories."
            ) from None
