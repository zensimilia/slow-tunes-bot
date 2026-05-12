from typing import TYPE_CHECKING

from .like import LikeStore
from .match import MatchStore
from .user import UserStore

if TYPE_CHECKING:
    from db.storage import StorageProtocol


class MasterStorage:
    def __init__(self, storage: StorageProtocol) -> None:
        self.user = UserStore(storage)
        self.match = MatchStore(storage)
        self.like = LikeStore(storage)
