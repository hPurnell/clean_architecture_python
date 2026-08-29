# Free of transport concepts on purpose: nothing in a domain or service module
# should raise an HTTPException. The web layer maps these to status codes in
# app.shared.web.exception_handlers; the messaging layer lets them propagate.
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
