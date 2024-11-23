from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from sqlmodel import Field, SQLModel


class ItemBase(SQLModel):
    key: str
    data: str


class Item(ItemBase, table=True):  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=ZoneInfo("America/New_York"))
    )


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: int
    created_at: datetime
