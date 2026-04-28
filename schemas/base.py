from datetime import datetime  # noqa: TC003

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    pk: int
    created_at: datetime
    updated_at: datetime
