# ruff: noqa: UP037
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .like import LikeModel
    from .match import MatchModel


class UserModel(BaseModel):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=True)

    matches: Mapped[list["MatchModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[list["LikeModel"]] = relationship(back_populates="user", cascade="all, delete-orphan")
