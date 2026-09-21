from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class IssueTypeBase(BaseModel):
    category: str = Field(min_length=2, max_length=100)
    sub_type: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    requires_verification: bool = True
    is_active: bool = True


class IssueTypeCreate(IssueTypeBase):
    pass


class IssueTypeUpdate(BaseModel):
    category: Optional[str] = Field(default=None, min_length=2, max_length=100)
    sub_type: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    requires_verification: Optional[bool] = None
    is_active: Optional[bool] = None


class IssueTypeOut(IssueTypeBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
