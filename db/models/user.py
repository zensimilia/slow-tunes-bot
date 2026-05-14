from typing import TYPE_CHECKING

from sqlmodel import JSON, Field, Relationship, SQLModel

from bot.services.ffmpeg import FxAnalog  # noqa: TC001

from .base import BaseModel, Timestamped

if TYPE_CHECKING:
    from .like import Like
    from .match import Match

DEFAULT_USERNAME = "Private Person"


class UserOptions(BaseModel):
    fx_analog: FxAnalog | None = None


class UserNew(SQLModel):
    tg_id: int = Field(unique=True, index=True, nullable=False)
    username: str | None = Field(default=DEFAULT_USERNAME, nullable=True)
    options: UserOptions = Field(default_factory=UserOptions, sa_type=JSON)


class User(UserNew, Timestamped, BaseModel, table=True):
    __tablename__: str = "users"

    pk: int = Field(default=None, primary_key=True)

    matches: list[Match] = Relationship(back_populates="user")
    likes: list[Like] = Relationship(back_populates="user", cascade_delete=True)


class UserUpdate(SQLModel):
    username: str
    options: UserOptions = Field(default_factory=UserOptions, sa_type=JSON)
