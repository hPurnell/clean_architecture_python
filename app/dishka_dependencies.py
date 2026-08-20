from collections.abc import Iterator

from dishka import Provider, Scope, provide, from_context

from app.auth.domain import AbstractUserRepository
from app.auth.db.fake_user_respository import FakeUserRepository
from app.items.domain import AbstractUnitOfWork, AbstractItemCommandPublisher
from app.items.service import UnitOfWork, FakeUnitOfWork, ItemCommandPublisher
from app.faststream_app_factory import FastStreamBroker


class AppProvider(Provider):
    broker = from_context(provides=FastStreamBroker, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    async def user_repository(self) -> AbstractUserRepository:
        return FakeUserRepository()

    @provide(scope=Scope.REQUEST)
    def unit_of_work(self) -> Iterator[AbstractUnitOfWork]:
        with UnitOfWork() as unit_of_work:
            yield unit_of_work

    @provide(scope=Scope.REQUEST)
    async def item_command_publisher(
        self, broker: FastStreamBroker
    ) -> AbstractItemCommandPublisher:
        return ItemCommandPublisher(broker)


class UnitTestProvider(Provider):
    broker = from_context(provides=FastStreamBroker, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    async def user_repository(self) -> AbstractUserRepository:
        return FakeUserRepository()

    @provide(scope=Scope.REQUEST)
    def unit_of_work(self) -> Iterator[AbstractUnitOfWork]:
        with FakeUnitOfWork() as unit_of_work:
            yield unit_of_work

    @provide(scope=Scope.REQUEST)
    async def item_command_publisher(
        self, broker: FastStreamBroker
    ) -> AbstractItemCommandPublisher:
        return ItemCommandPublisher(broker)


class IntegrationTestProvider(Provider):
    broker = from_context(provides=FastStreamBroker, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    async def user_repository(self) -> AbstractUserRepository:
        return FakeUserRepository()

    @provide(scope=Scope.REQUEST)
    def unit_of_work(self) -> Iterator[AbstractUnitOfWork]:
        with FakeUnitOfWork() as unit_of_work:
            yield unit_of_work

    @provide(scope=Scope.REQUEST)
    async def item_command_publisher(
        self, broker: FastStreamBroker
    ) -> AbstractItemCommandPublisher:
        return ItemCommandPublisher(broker)
