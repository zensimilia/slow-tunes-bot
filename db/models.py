from datetime import datetime
from typing import List

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, func
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BaseModel(AsyncAttrs, DeclarativeBase):
    pk: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(BaseModel):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=True)

    matches: Mapped[List["Match"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    likes: Mapped[List["Like"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Match(BaseModel):
    __tablename__ = "matches"

    original_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        unique=True,
        index=True,
    )
    slowed_id: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    private: Mapped[bool] = mapped_column(Boolean, default=True)
    forbidden: Mapped[bool] = mapped_column(Boolean, default=False)
    user_pk: Mapped[int] = mapped_column(ForeignKey("users.pk", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="matches")
    likes: Mapped[List["Like"]] = relationship(
        back_populates="match", cascade="all, delete-orphan"
    )


class Like(BaseModel):
    __tablename__ = "likes"

    user_pk: Mapped[int] = mapped_column(ForeignKey("users.pk", ondelete="CASCADE"))
    match_pk: Mapped[int] = mapped_column(ForeignKey("matches.pk", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="likes")
    match: Mapped["Match"] = relationship(back_populates="likes")
