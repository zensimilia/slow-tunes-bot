from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .base import BaseModel

if TYPE_CHECKING:
    from .like import Like
    from .user import User


class Match(BaseModel, table=True):
    __tablename__: str = "matches"

    original_id: str = Field(nullable=False, unique=True, index=True)
    slowed_id: str = Field(nullable=False, unique=True)
    is_private: bool = Field(default=True)
    is_forbidden: bool = Field(default=False)
    user_pk: int = Field(foreign_key="users.pk", ondelete="CASCADE")

    user: User = Relationship(back_populates="matches")
    likes: list[Like] | None = Relationship(back_populates="match", cascade_delete=True)


class MatchNew(SQLModel):
    user_pk: int
    original_id: str
    slowed_id: str = "PENDING"
    is_private: bool = True
    is_forbidden: bool = False
