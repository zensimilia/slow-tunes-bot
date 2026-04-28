from pydantic import BaseModel

from .base import BaseSchema


class MatchNew(BaseModel):
    original_id: str
    slowed_id: str
    is_private: bool = True
    is_forbidden: bool = False
    user_pk: int


class MatchRead(MatchNew, BaseSchema): ...
