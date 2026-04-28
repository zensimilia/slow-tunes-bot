# ruff: noqa: UP037
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .like import LikeModel
    from .user import UserModel


class MatchModel(BaseModel):
    __tablename__ = "matches"

    original_id: Mapped[str] = mapped_column(String, nullable=False, unique=True, index=True)
    slowed_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=True)
    is_forbidden: Mapped[bool] = mapped_column(Boolean, default=False)
    user_pk: Mapped[int] = mapped_column(ForeignKey("users.pk", ondelete="CASCADE"))

    user: Mapped["UserModel"] = relationship(back_populates="matches")
    likes: Mapped[list["LikeModel"]] = relationship(back_populates="match", cascade="all, delete-orphan")
