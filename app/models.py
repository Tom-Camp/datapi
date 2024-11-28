from datetime import datetime
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo

from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel


class ItemBase(SQLModel):
    key: str
    data: Dict[str, Any] = Field(sa_type=JSON, default={})


class Item(ItemBase, table=True):  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=ZoneInfo("America/New_York"))
    )


class ItemCreate(ItemBase):
    pass


class ItemResponse(ItemBase):
    id: Optional[int]
    key: str
    data: Dict
