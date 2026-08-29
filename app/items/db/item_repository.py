import datetime

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import Session

from app.items.domain.abstract_item_repository import AbstractItemRepository
from app.items.domain.item import Item
from app.shared.persistence.base import Base
from app.shared.persistence.repository import BaseRepository


class ItemEntity(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    value_str = Column(String(255), nullable=True)
    value_int = Column(Integer, nullable=True)
    value_float = Column(Float, nullable=True)
    created_date = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    modified_date = Column(
        DateTime,
        nullable=False,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
    )


class ItemRepository(BaseRepository[ItemEntity, Item], AbstractItemRepository):
    def __init__(self, session: Session):
        super().__init__(session, ItemEntity, Item)
