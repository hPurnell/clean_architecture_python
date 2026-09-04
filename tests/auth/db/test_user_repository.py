from collections.abc import Iterator
from dataclasses import replace

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.auth.db.user_repository import UserRepository
from app.auth.domain.abstract_user_repository import AbstractUserRepository
from app.auth.domain.user import User
from app.shared.clock import utc_now
from app.shared.persistence.entities import Base
from app.shared.persistence.unit_of_work import SqlAlchemyUnitOfWork


@pytest.fixture
def unit_of_work() -> Iterator[SqlAlchemyUnitOfWork]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    factory: sessionmaker[Session] = sessionmaker(bind=engine)
    with SqlAlchemyUnitOfWork(
        factory, {AbstractUserRepository: UserRepository}
    ) as unit_of_work:
        yield unit_of_work


def a_user(username: str = "ada@example.com") -> User:
    now = utc_now()
    return User(
        id=username.replace("@", "").replace(".", "")[:32],
        name="Ada",
        username=username,
        password_hash="$argon2id$not-a-real-hash",
        created_date=now,
        modified_date=now,
    )


@pytest.mark.integration
class TestUserRepository:
    def test_a_stored_user_reads_back(self, unit_of_work):
        users = unit_of_work.repository(AbstractUserRepository)
        users.add(a_user())
        unit_of_work.commit()

        stored = users.get_user("ada@example.com")
        assert stored is not None
        assert stored.name == "Ada"

    def test_an_unknown_username_is_none(self, unit_of_work):
        users = unit_of_work.repository(AbstractUserRepository)

        assert users.get_user("nobody@example.com") is None

    def test_a_changed_password_hash_is_stored(self, unit_of_work):
        users = unit_of_work.repository(AbstractUserRepository)
        user = users.add(a_user())
        unit_of_work.commit()

        users.update(replace(user, password_hash="$argon2id$a-new-hash"))
        unit_of_work.commit()

        stored = users.get_user("ada@example.com")
        assert stored is not None
        assert stored.password_hash == "$argon2id$a-new-hash"

    def test_the_same_username_cannot_be_registered_twice(self, unit_of_work):
        # Enforced by the schema, so two registrations racing each other cannot
        # both pass the service's check and both insert.
        users = unit_of_work.repository(AbstractUserRepository)
        users.add(a_user())
        unit_of_work.commit()

        with pytest.raises(IntegrityError):
            users.add(replace(a_user(), id="a-different-id"))
