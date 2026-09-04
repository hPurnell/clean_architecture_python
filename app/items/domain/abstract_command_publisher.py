from abc import ABC, abstractmethod

from app.items.domain.item import Item


class AbstractItemCommandPublisher(ABC):
    """Port for dispatching item commands to another process.

    Takes domain objects, so the domain never sees a message schema. The
    ``job_id`` is carried through so the outcome can be reported against it.
    """

    @abstractmethod
    async def create_item(self, item: Item, job_id: str) -> None: ...

    @abstractmethod
    async def update_item(self, item: Item, job_id: str) -> None: ...

    @abstractmethod
    async def delete_item(self, item_id: int, job_id: str) -> None: ...
