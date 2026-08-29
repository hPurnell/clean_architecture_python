from app.shared.domain.errors import NotFoundError, PersistenceError, ValidationError


class ItemNotFoundError(NotFoundError):
    def __init__(self, item_id: int | None) -> None:
        super().__init__(f"Item not found: {item_id}")
        self.item_id = item_id


class ItemNotPersistedError(PersistenceError):
    """The repository declined to store the item."""


class ItemIdRequiredError(ValidationError):
    def __init__(self) -> None:
        super().__init__("An item id is required for this operation.")
