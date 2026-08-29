from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")
ID = TypeVar("ID")


class AbstractRepository(ABC, Generic[T, ID]):
    @abstractmethod
    def create(self, obj: T) -> T: ...

    @abstractmethod
    def get(self, obj_id: ID) -> Optional[T]: ...

    @abstractmethod
    def update(self, obj: T) -> Optional[T]: ...

    @abstractmethod
    def delete(self, obj_id: ID) -> bool: ...

    @abstractmethod
    def get_all(self) -> List[T]: ...
