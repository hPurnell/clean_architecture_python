from datetime import datetime

from sqlalchemy import ForeignKey, String, delete, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.auth.domain.abstract_user_repository import AbstractUserRepository
from app.auth.domain.role import Role
from app.auth.domain.user import User
from app.shared.persistence.base import Base


class UserEntity(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    # Unique in the schema, not just checked before an insert: two registrations
    # racing each other would both find the name free.
    username: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_date: Mapped[datetime] = mapped_column()
    modified_date: Mapped[datetime] = mapped_column()


class UserRoleEntity(Base):
    __tablename__ = "user_roles"

    # The pair is the key, so a role cannot be granted twice.
    user_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(32), primary_key=True)


class UserRepository(AbstractUserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_user(self, username: str) -> User | None:
        entity = self._session.execute(
            select(UserEntity).where(UserEntity.username == username)
        ).scalar_one_or_none()
        return self._to_user(entity) if entity else None

    def _roles_of(self, user_id: str) -> frozenset[Role]:
        # A second query rather than a relationship: the repository hands back a
        # plain dataclass, so nothing may be left to load lazily off a session
        # that has already been closed.
        rows = (
            self._session.execute(
                select(UserRoleEntity.role).where(UserRoleEntity.user_id == user_id)
            )
            .scalars()
            .all()
        )
        return frozenset(Role(role) for role in rows)

    def _store_roles(self, user: User) -> None:
        self._session.execute(
            delete(UserRoleEntity).where(UserRoleEntity.user_id == user.id)
        )
        for role in user.roles:
            self._session.add(UserRoleEntity(user_id=user.id, role=role.value))

    def add(self, user: User) -> User:
        self._session.add(
            UserEntity(
                id=user.id,
                name=user.name,
                username=user.username,
                password_hash=user.password_hash,
                created_date=user.created_date,
                modified_date=user.modified_date,
            )
        )
        self._session.flush()
        self._store_roles(user)
        self._session.flush()
        return user

    def update(self, user: User) -> User | None:
        entity = self._session.get(UserEntity, user.id)
        if entity is None:
            return None
        entity.name = user.name
        entity.username = user.username
        entity.password_hash = user.password_hash
        entity.modified_date = user.modified_date or entity.modified_date
        self._store_roles(user)
        self._session.flush()
        return self._to_user(entity)

    def _to_user(self, entity: UserEntity) -> User:
        return User(
            id=entity.id,
            name=entity.name,
            username=entity.username,
            password_hash=entity.password_hash,
            roles=self._roles_of(entity.id),
            created_date=entity.created_date,
            modified_date=entity.modified_date,
        )
