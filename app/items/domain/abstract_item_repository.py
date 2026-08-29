from app.items.domain.item import Item
from app.shared.domain.repository import AbstractRepository


class AbstractItemRepository(AbstractRepository[Item, int]):
    pass
