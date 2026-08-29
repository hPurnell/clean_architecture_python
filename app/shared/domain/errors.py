"""Domain-level error types.

These are deliberately free of any transport or framework concepts. The web
layer maps them onto HTTP status codes in
``app.shared.web.exception_handlers``; the messaging layer lets them propagate
to the broker. Nothing in a domain or service module should raise an
``HTTPException``.
"""


class DomainError(Exception):
    """Base class for every error the domain and service layers raise."""


class NotFoundError(DomainError):
    """A requested entity does not exist."""


class ValidationError(DomainError):
    """The caller supplied data the domain considers invalid."""


class ConflictError(DomainError):
    """The requested change conflicts with the current state."""


class AuthenticationError(DomainError):
    """The caller could not be authenticated."""


class PersistenceError(DomainError):
    """The repository failed to store an entity."""
