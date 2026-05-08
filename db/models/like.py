from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from .base import BaseModel, Timestamped

if TYPE_CHECKING:
    from .match import Match
    from .user import User


class LikeNew(SQLModel):
    user_pk: int
    match_pk: int


class Like(LikeNew, BaseModel, Timestamped, table=True):
    __tablename__: str = "likes"
    __table_args__ = (UniqueConstraint("user_pk", "match_pk", name="unique_user_match_like"),)

    pk: int = Field(default=None, primary_key=True)

    user_pk: int = Field(foreign_key="users.pk", ondelete="CASCADE")
    match_pk: int = Field(foreign_key="matches.pk", ondelete="CASCADE")

    user: User = Relationship(back_populates="likes")
    match: Match = Relationship(back_populates="likes")
