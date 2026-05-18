from typing import TYPE_CHECKING, Protocol, TypeVar

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

SessionT = TypeVar("SessionT")


class AsyncDatabaseProtocol[SessionT](Protocol):
    def get_session(self) -> AbstractAsyncContextManager[SessionT]: ...
