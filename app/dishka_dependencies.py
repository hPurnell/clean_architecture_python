from collections.abc import Iterator
from typing import Any, Callable, Mapping, Type

from dishka import Provider, Scope, from_context, provide
from sqlalchemy.orm import Session, sessionmaker

from app.auth.db.fake_user_repository import FakeUserRepository
from app.auth.db.user_repository import UserRepository
from app.auth.domain.abstract_auth_service import AbstractAuthService
from app.auth.domain.abstract_password_service import AbstractPasswordService
from app.auth.domain.abstract_token_service import AbstractTokenService
from app.auth.domain.abstract_user_repository import AbstractUserRepository
from app.auth.service.argon2_password_service import Argon2PasswordService
from app.auth.service.auth_service import AuthService
from app.auth.service.jwt_token_service import JwtTokenService
from app.broker import Broker
from app.config import AppConfig, config
from app.items.db.fake_item_repository import FakeItemRepository
from app.items.db.item_repository import ItemRepository
from app.items.domain.abstract_command_publisher import AbstractItemCommandPublisher
from app.items.domain.abstract_item_repository import AbstractItemRepository
from app.items.messaging.item_command_publisher import ItemCommandPublisher
from app.items.service.item_command_dispatcher import ItemCommandDispatcher
from app.items.service.item_service import ItemService
from app.jobs.db.fake_job_repository import FakeJobRepository
from app.jobs.db.job_repository import JobRepository
from app.jobs.domain.abstract_job_repository import AbstractJobRepository
from app.jobs.service.job_service import JobService
from app.shared.domain.unit_of_work import AbstractUnitOfWork
from app.shared.persistence.engine import create_session_factory
from app.shared.persistence.in_memory_unit_of_work import InMemoryUnitOfWork
from app.shared.persistence.unit_of_work import SqlAlchemyUnitOfWork

# Repository port -> factory taking the unit of work's session. An aggregate
# is added here; the unit of work itself does not change.
REPOSITORY_FACTORIES: Mapping[Type[Any], Callable[[Session], Any]] = {
    AbstractItemRepository: ItemRepository,
    AbstractJobRepository: JobRepository,
    AbstractUserRepository: UserRepository,
}


class AppProvider(Provider):
    broker = from_context(provides=Broker, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def app_config(self) -> AppConfig:
        return config

    @provide(scope=Scope.APP)
    def session_factory(self, app_config: AppConfig) -> sessionmaker[Session]:
        return create_session_factory(
            app_config.DATABASE_URL, app_config.DATABASE_ISOLATION_LEVEL
        )

    @provide(scope=Scope.APP)
    def token_service(self, app_config: AppConfig) -> AbstractTokenService:
        return JwtTokenService(secret=app_config.JWT_SECRET)

    @provide(scope=Scope.APP)
    def password_service(self) -> AbstractPasswordService:
        return Argon2PasswordService()

    @provide(scope=Scope.REQUEST)
    def unit_of_work(
        self, session_factory: sessionmaker[Session]
    ) -> Iterator[AbstractUnitOfWork]:
        with SqlAlchemyUnitOfWork(
            session_factory, REPOSITORY_FACTORIES
        ) as unit_of_work:
            yield unit_of_work

    @provide(scope=Scope.REQUEST)
    def item_service(self, unit_of_work: AbstractUnitOfWork) -> ItemService:
        return ItemService(unit_of_work)

    @provide(scope=Scope.REQUEST)
    def job_service(self, unit_of_work: AbstractUnitOfWork) -> JobService:
        return JobService(unit_of_work)

    @provide(scope=Scope.REQUEST)
    def item_command_dispatcher(
        self,
        item_command_publisher: AbstractItemCommandPublisher,
        job_service: JobService,
    ) -> ItemCommandDispatcher:
        return ItemCommandDispatcher(item_command_publisher, job_service)

    @provide(scope=Scope.REQUEST)
    def auth_service(
        self,
        unit_of_work: AbstractUnitOfWork,
        token_service: AbstractTokenService,
        password_service: AbstractPasswordService,
    ) -> AbstractAuthService:
        return AuthService(unit_of_work, token_service, password_service)

    @provide(scope=Scope.REQUEST)
    def item_command_publisher(
        self,
        # Picked from configuration at import time, so a variable to mypy.
        broker: Broker,  # type: ignore[valid-type]
    ) -> AbstractItemCommandPublisher:
        return ItemCommandPublisher(broker)


class UnitTestProvider(Provider):
    broker = from_context(provides=Broker, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def app_config(self) -> AppConfig:
        return config

    @provide(scope=Scope.APP)
    def token_service(self, app_config: AppConfig) -> AbstractTokenService:
        return JwtTokenService(secret=app_config.JWT_SECRET)

    @provide(scope=Scope.APP)
    def password_service(self) -> AbstractPasswordService:
        return Argon2PasswordService()

    # App scope, so each test's app gets its own store and shares no state.
    @provide(scope=Scope.APP)
    def fake_item_repository(self) -> FakeItemRepository:
        return FakeItemRepository()

    @provide(scope=Scope.APP)
    def fake_job_repository(self) -> FakeJobRepository:
        return FakeJobRepository()

    @provide(scope=Scope.APP)
    def fake_user_repository(self) -> FakeUserRepository:
        return FakeUserRepository()

    @provide(scope=Scope.REQUEST)
    def unit_of_work(
        self,
        item_repository: FakeItemRepository,
        job_repository: FakeJobRepository,
        user_repository: FakeUserRepository,
    ) -> Iterator[AbstractUnitOfWork]:
        with InMemoryUnitOfWork(
            {
                AbstractItemRepository: item_repository,
                AbstractJobRepository: job_repository,
                AbstractUserRepository: user_repository,
            }
        ) as unit_of_work:
            yield unit_of_work

    @provide(scope=Scope.REQUEST)
    def item_service(self, unit_of_work: AbstractUnitOfWork) -> ItemService:
        return ItemService(unit_of_work)

    @provide(scope=Scope.REQUEST)
    def job_service(self, unit_of_work: AbstractUnitOfWork) -> JobService:
        return JobService(unit_of_work)

    @provide(scope=Scope.REQUEST)
    def item_command_dispatcher(
        self,
        item_command_publisher: AbstractItemCommandPublisher,
        job_service: JobService,
    ) -> ItemCommandDispatcher:
        return ItemCommandDispatcher(item_command_publisher, job_service)

    @provide(scope=Scope.REQUEST)
    def auth_service(
        self,
        unit_of_work: AbstractUnitOfWork,
        token_service: AbstractTokenService,
        password_service: AbstractPasswordService,
    ) -> AbstractAuthService:
        return AuthService(unit_of_work, token_service, password_service)

    @provide(scope=Scope.REQUEST)
    def item_command_publisher(
        self,
        # Picked from configuration at import time, so a variable to mypy.
        broker: Broker,  # type: ignore[valid-type]
    ) -> AbstractItemCommandPublisher:
        return ItemCommandPublisher(broker)


class IntegrationTestProvider(Provider):
    broker = from_context(provides=Broker, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def app_config(self) -> AppConfig:
        return config

    @provide(scope=Scope.APP)
    def token_service(self, app_config: AppConfig) -> AbstractTokenService:
        return JwtTokenService(secret=app_config.JWT_SECRET)

    @provide(scope=Scope.APP)
    def password_service(self) -> AbstractPasswordService:
        return Argon2PasswordService()

    @provide(scope=Scope.APP)
    def fake_item_repository(self) -> FakeItemRepository:
        return FakeItemRepository()

    @provide(scope=Scope.APP)
    def fake_job_repository(self) -> FakeJobRepository:
        return FakeJobRepository()

    @provide(scope=Scope.APP)
    def fake_user_repository(self) -> FakeUserRepository:
        return FakeUserRepository()

    @provide(scope=Scope.REQUEST)
    def unit_of_work(
        self,
        item_repository: FakeItemRepository,
        job_repository: FakeJobRepository,
        user_repository: FakeUserRepository,
    ) -> Iterator[AbstractUnitOfWork]:
        with InMemoryUnitOfWork(
            {
                AbstractItemRepository: item_repository,
                AbstractJobRepository: job_repository,
                AbstractUserRepository: user_repository,
            }
        ) as unit_of_work:
            yield unit_of_work

    @provide(scope=Scope.REQUEST)
    def item_service(self, unit_of_work: AbstractUnitOfWork) -> ItemService:
        return ItemService(unit_of_work)

    @provide(scope=Scope.REQUEST)
    def job_service(self, unit_of_work: AbstractUnitOfWork) -> JobService:
        return JobService(unit_of_work)

    @provide(scope=Scope.REQUEST)
    def item_command_dispatcher(
        self,
        item_command_publisher: AbstractItemCommandPublisher,
        job_service: JobService,
    ) -> ItemCommandDispatcher:
        return ItemCommandDispatcher(item_command_publisher, job_service)

    @provide(scope=Scope.REQUEST)
    def auth_service(
        self,
        unit_of_work: AbstractUnitOfWork,
        token_service: AbstractTokenService,
        password_service: AbstractPasswordService,
    ) -> AbstractAuthService:
        return AuthService(unit_of_work, token_service, password_service)

    @provide(scope=Scope.REQUEST)
    def item_command_publisher(
        self,
        # Picked from configuration at import time, so a variable to mypy.
        broker: Broker,  # type: ignore[valid-type]
    ) -> AbstractItemCommandPublisher:
        return ItemCommandPublisher(broker)
