from typing import TYPE_CHECKING

from .like import LikeStore
from .match import MatchStore
from .user import UserStore

if TYPE_CHECKING:
    from bot.core.storage import AsyncStorageProtocol


class MasterStorage:
    def __init__(self, storage: AsyncStorageProtocol) -> None:
        self.user = UserStore(storage)
        self.match = MatchStore(storage)
        self.like = LikeStore(storage)
