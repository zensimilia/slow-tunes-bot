# ruff: noqa: UP037
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .match import MatchModel
    from .user import UserModel


class LikeModel(BaseModel):
    __tablename__ = "likes"

    user_pk: Mapped[int] = mapped_column(ForeignKey("users.pk", ondelete="CASCADE"))
    match_pk: Mapped[int] = mapped_column(ForeignKey("matches.pk", ondelete="CASCADE"))

    user: Mapped["UserModel"] = relationship(back_populates="likes")
    match: Mapped["MatchModel"] = relationship(back_populates="likes")
