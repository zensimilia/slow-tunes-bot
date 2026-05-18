from datetime import UTC, datetime

from pydantic import BaseModel, Field

DEFAULT_USERNAME = "Private Person"


class TimestampedDomain(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class UserOptionsDomain(BaseModel):
    fx_analog: str | None = None


class UserNewDomain(BaseModel):
    tg_id: str
    username: str | None = Field(default=DEFAULT_USERNAME)
    options: UserOptionsDomain = Field(default_factory=UserOptionsDomain)


class UserDomain(UserNewDomain, TimestampedDomain):
    pk: int


class UserUpdateDomain(BaseModel):
    username: str
    options: UserOptionsDomain | None = None


class MatchNewDomain(BaseModel):
    original_id: str
    slowed_id: str
    is_private: bool = Field(default=True)
    is_forbidden: bool = Field(default=False)
    user_id: str


class MatchDomain(MatchNewDomain, TimestampedDomain):
    pk: int


class MatchUpdateDomain(BaseModel):
    original_id: str | None = None
    slowed_id: str | None = None
    is_private: bool | None = None
    is_forbidden: bool | None = None


class LikeNewDomain(BaseModel):
    user_pk: int
    match_pk: int


class LikeDomain(LikeNewDomain, TimestampedDomain):
    pk: int
