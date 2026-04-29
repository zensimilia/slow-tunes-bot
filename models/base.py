from datetime import datetime  # noqa: TC003

from sqlmodel import Field, SQLModel, func


class BaseModel(SQLModel):
    pk: int | None = Field(
        default=None,
        primary_key=True,
    )
    created_at: datetime | None = Field(
        default_factory=func.now,
        sa_column_kwargs={
            "nullable": False,
        },
    )
    updated_at: datetime | None = Field(
        default_factory=func.now,
        sa_column_kwargs={
            "onupdate": func.now(),
            "nullable": False,
        },
    )
