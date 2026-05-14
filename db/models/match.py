from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from .base import BaseModel, Timestamped

if TYPE_CHECKING:
    from .like import Like
    from .user import User


class MatchNew(SQLModel):
    original_id: str = Field(nullable=False, index=True)
    slowed_id: str = Field(nullable=False)
    is_private: bool = Field(default=True)
    is_forbidden: bool = Field(default=False)
    user_id: int = Field(foreign_key="users.tg_id", ondelete="CASCADE")


class Match(MatchNew, BaseModel, Timestamped, table=True):
    __tablename__: str = "matches"
    __table_args__ = (UniqueConstraint("user_id", "original_id", name="unique_user_match_like"),)

    pk: int = Field(default=None, primary_key=True)

    user: User = Relationship(back_populates="matches")
    likes: list[Like] | None = Relationship(back_populates="match", cascade_delete=True)


class MatchUpdate(SQLModel):
    original_id: str | None = None
    slowed_id: str | None = None
    is_private: bool | None = None
    is_forbidden: bool | None = None
