import logging
from collections.abc import Callable, MutableMapping
from typing import Any

from litestar import Request, Response
from litestar.status_codes import (
    HTTP_400_BAD_REQUEST,
    HTTP_401_UNAUTHORIZED,
    HTTP_404_NOT_FOUND,
    HTTP_409_CONFLICT,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.shared.domain.errors import (
    AuthenticationError,
    ConflictError,
    DomainError,
    NotFoundError,
    PersistenceError,
    ValidationError,
)

logger = logging.getLogger(__name__)

# Checked in order, so subclasses must precede their base classes.
_STATUS_BY_ERROR: tuple[tuple[type[DomainError], int], ...] = (
    (NotFoundError, HTTP_404_NOT_FOUND),
    (AuthenticationError, HTTP_401_UNAUTHORIZED),
    (ConflictError, HTTP_409_CONFLICT),
    (ValidationError, HTTP_400_BAD_REQUEST),
    (PersistenceError, HTTP_500_INTERNAL_SERVER_ERROR),
)

DEFAULT_STATUS_CODE = HTTP_400_BAD_REQUEST


def status_code_for(exc: DomainError) -> int:
    for error_type, status_code in _STATUS_BY_ERROR:
        if isinstance(exc, error_type):
            return status_code
    return DEFAULT_STATUS_CODE


def domain_error_handler(
    request: Request[Any, Any, Any], exc: DomainError
) -> Response[Any]:
    status_code = status_code_for(exc)
    if status_code >= HTTP_500_INTERNAL_SERVER_ERROR:
        logger.exception("Unhandled domain error on %s", request.url.path)
    else:
        logger.info("%s on %s: %s", type(exc).__name__, request.url.path, exc)
    return Response(
        content={"status_code": status_code, "detail": str(exc)},
        status_code=status_code,
    )


# Typed as Litestar takes it: the mapping is keyed by status code or exception
# type, and this application registers one entry.
EXCEPTION_HANDLERS: MutableMapping[
    int | type[Exception], Callable[[Request[Any, Any, Any], Any], Response[Any]]
] = {DomainError: domain_error_handler}
