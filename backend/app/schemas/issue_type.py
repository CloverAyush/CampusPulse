from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class IssueTypeBase(BaseModel):
    category: str
    sub_type: str
    description: Optional[str] = None
    requires_verification: bool = True
    is_active: bool = True

class IssueTypeCreate(IssueTypeBase):
    pass

class IssueTypeUpdate(BaseModel):
    category: Optional[str] = None
    sub_type: Optional[str] = None
    description: Optional[str] = None
    requires_verification: Optional[bool] = None
    is_active: Optional[bool] = None

class IssueTypeOut(IssueTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

