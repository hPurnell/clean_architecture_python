from dataclasses import asdict, fields
from typing import TYPE_CHECKING, Any, Generic, List, Optional, Type, TypeVar, Union

from sqlalchemy import select
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from _typeshed import DataclassInstance

TEntity = TypeVar("TEntity")
# Every mapped dataclass, so that asdict() and fields() apply to it.
TDataclass = TypeVar("TDataclass", bound="DataclassInstance")


class BaseRepository(Generic[TEntity, TDataclass]):
    def __init__(
        self,
        session: Session,
        entity_class: Type[TEntity],
        dataclass_class: Type[TDataclass],
        pk_fields: Optional[list[str]] = None,
    ):
        self.session = session
        self.entity_class = entity_class
        self.dataclass_class = dataclass_class

        if pk_fields:
            self.pk_fields = pk_fields
        else:
            mapper = inspect(self.entity_class)
            if mapper is None:
                raise ValueError("Entity is not a mapped class.")
            self.pk_fields = [col.name for col in mapper.primary_key]
            if not self.pk_fields:
                raise ValueError("Entity has no primary key fields.")

    def _map_to_dataclass(self, entity: TEntity) -> TDataclass:
        return self.dataclass_class(
            **{
                key: value
                for key, value in entity.__dict__.items()
                if not key.startswith("_")
            }
        )

    def _get_pk_values(self, dataclass_instance: TDataclass) -> dict[str, Any]:
        return {field: getattr(dataclass_instance, field) for field in self.pk_fields}

    def _get_entity_by_pk(
        self, pk_values: Union[Any, dict[str, Any]]
    ) -> Optional[TEntity]:
        if isinstance(pk_values, dict):
            # Ensure all primary key fields are present in the input dictionary.
            missing_fields = [
                field for field in self.pk_fields if field not in pk_values
            ]
            if missing_fields:
                raise ValueError(f"Missing primary key fields: {missing_fields}")

            # Create the dictionary directly, no need to convert it to a tuple
            pk_dict = {field: pk_values[field] for field in self.pk_fields}

        else:
            # For a single value as primary key input
            if len(self.pk_fields) != 1:
                raise ValueError(
                    "Expected composite key (dict with fields "
                    f"{self.pk_fields}), but got a single value."
                )
            pk_dict = {self.pk_fields[0]: pk_values}

        # Use the named primary key dictionary for session.get
        return self.session.get(self.entity_class, pk_dict)

    def create(self, dataclass_instance: TDataclass) -> TDataclass:
        entity = self.entity_class(**asdict(dataclass_instance))
        self.session.add(entity)
        self.session.flush()
        return self._map_to_dataclass(entity)

    def get(
        self, pk_values: Union[Any, tuple[Any, ...], dict[str, Any]]
    ) -> Optional[TDataclass]:
        entity = self._get_entity_by_pk(pk_values)
        return self._map_to_dataclass(entity) if entity else None

    def update(self, dataclass_instance: TDataclass) -> Optional[TDataclass]:
        pk_dict = self._get_pk_values(dataclass_instance)
        entity = self._get_entity_by_pk(pk_dict)
        if entity:
            for field in fields(dataclass_instance):
                setattr(entity, field.name, getattr(dataclass_instance, field.name))
            self.session.flush()
            return self._map_to_dataclass(entity)
        return None

    def delete(self, pk_values: Union[Any, tuple[Any, ...], dict[str, Any]]) -> bool:
        entity = self._get_entity_by_pk(pk_values)
        if entity:
            self.session.delete(entity)
            self.session.flush()
            return True
        return False

    def get_all(self) -> List[TDataclass]:
        result = self.session.execute(select(self.entity_class))
        entities = result.scalars().all()
        return [self._map_to_dataclass(entity) for entity in entities]
