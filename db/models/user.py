from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel, Timestamped

if TYPE_CHECKING:
    from .like import Like
    from .match import Match

DEFAULT_USERNAME = "Private Person"


class UserNew(SQLModel):
    tg_id: int = Field(unique=True, index=True, nullable=False)
    username: str = Field(default=DEFAULT_USERNAME, nullable=True)


class User(UserNew, Timestamped, BaseModel, table=True):
    __tablename__: str = "users"

    pk: int = Field(default=None, primary_key=True)

    matches: list[Match] = Relationship(back_populates="user")
    likes: list[Like] = Relationship(back_populates="user", cascade_delete=True)


class UserUpdate(SQLModel):
    username: str
