from pydantic import BaseModel

from .base import BaseSchema


class UserNew(BaseModel):
    tg_id: int
    username: str | None = None


class UserRead(UserNew, BaseSchema): ...
