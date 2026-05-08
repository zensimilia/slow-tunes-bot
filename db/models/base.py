from datetime import datetime  # noqa: TC003

from sqlmodel import Field, SQLModel, func


class BaseModel(SQLModel): ...


class Timestamped(SQLModel):
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
