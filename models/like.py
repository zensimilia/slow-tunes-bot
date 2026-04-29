from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .match import Match
    from .user import User


class Like(BaseModel, table=True):
    __tablename__: str = "likes"

    user_pk: int = Field(foreign_key="users.pk", ondelete="CASCADE")
    match_pk: int = Field(foreign_key="matches.pk", ondelete="CASCADE")

    user: User = Relationship(back_populates="likes")
    match: Match = Relationship(back_populates="likes")


class LikeNew(SQLModel):
    user_pk: int
    match_pk: int
