# Free of transport concepts: the web layer maps these to status codes, and
# the messaging layer lets them propagate.
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
