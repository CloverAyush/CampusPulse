from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class LocationBase(BaseModel):
    name: str
    code: str
    building: str
    floor: Optional[str] = None
    room: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None

class LocationOut(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class LocationHierarchyOut(LocationOut):
    model_config = ConfigDict(from_attributes=True)
    children: List["LocationHierarchyOut"] = []

