from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .like import Like
    from .match import Match


class User(BaseModel, table=True):
    __tablename__: str = "users"

    tg_id: int = Field(unique=True, index=True, nullable=False)
    username: str = Field(nullable=True)

    matches: list[Match] = Relationship(back_populates="user")
    likes: list[Like] = Relationship(back_populates="user", cascade_delete=True)


class UserNew(SQLModel):
    tg_id: int
    username: str | None = None


class UserUpdate(SQLModel):
    username: str
