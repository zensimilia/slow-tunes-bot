from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class GeneralModel(BaseModel):
    pk: int
    created_at: datetime
    updated_at: datetime


class NewUser(BaseModel):
    tg_id: int
    username: Optional[str] = None


class GetUser(NewUser, GeneralModel):
    model_config = ConfigDict(from_attributes=True)


class NewMatch(BaseModel):
    original_id: str
    slowed_id: str
    private: bool = True
    forbidden: bool = False
    user_pk: int


class GetMatch(NewMatch, GeneralModel):
    model_config = ConfigDict(from_attributes=True)
