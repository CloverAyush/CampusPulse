from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LocationBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    code: str = Field(min_length=2, max_length=50, pattern=r"^[A-Za-z0-9._\-]+$")
    building: str = Field(min_length=1, max_length=100)
    floor: Optional[str] = Field(default=None, max_length=50)
    room: Optional[str] = Field(default=None, max_length=50)
    parent_id: Optional[int] = Field(default=None, ge=1)
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    code: Optional[str] = Field(default=None, min_length=2, max_length=50, pattern=r"^[A-Za-z0-9._\-]+$")
    building: Optional[str] = Field(default=None, min_length=1, max_length=100)
    floor: Optional[str] = Field(default=None, max_length=50)
    room: Optional[str] = Field(default=None, max_length=50)
    parent_id: Optional[int] = Field(default=None, ge=1)
    is_active: Optional[bool] = None


class LocationOut(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class LocationHierarchyOut(LocationOut):
    model_config = ConfigDict(from_attributes=True)
    children: List["LocationHierarchyOut"] = []
