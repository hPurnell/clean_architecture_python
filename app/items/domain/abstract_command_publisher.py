from abc import ABC, abstractmethod

from app.items.domain.item import Item


class AbstractItemCommandPublisher(ABC):
    """Port for dispatching item commands to another process.

    Implementations accept domain objects; translating them into wire-format
    messages is the adapter's job, so the domain never sees a message schema.

    Every method takes the id of the job the command belongs to. The publisher
    does not interpret it — it is carried through to whoever runs the command,
    so that the outcome can be reported against the handle the caller was
    given.
    """

    @abstractmethod
    async def create_item(self, item: Item, job_id: str) -> None: ...

    @abstractmethod
    async def update_item(self, item: Item, job_id: str) -> None: ...

    @abstractmethod
    async def delete_item(self, item_id: int, job_id: str) -> None: ...
