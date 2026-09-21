from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.issue_type import IssueTypeOut
from app.schemas.location import LocationOut
from app.schemas.user import UserPublic


class RoutingRuleBase(BaseModel):
    issue_type_id: Optional[int] = Field(default=None, ge=1)
    location_id: Optional[int] = Field(default=None, ge=1)
    handler_id: int = Field(ge=1)
    priority: int = Field(default=10, ge=0, le=1000)
    is_active: bool = True


class RoutingRuleCreate(RoutingRuleBase):
    pass


class RoutingRuleUpdate(BaseModel):
    issue_type_id: Optional[int] = Field(default=None, ge=1)
    location_id: Optional[int] = Field(default=None, ge=1)
    handler_id: Optional[int] = Field(default=None, ge=1)
    priority: Optional[int] = Field(default=None, ge=0, le=1000)
    is_active: Optional[bool] = None


class RoutingRuleOut(RoutingRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    handler: Optional[UserPublic] = None
    issue_type: Optional[IssueTypeOut] = None
    location: Optional[LocationOut] = None


class RoutingPreview(BaseModel):
    issue_type_id: int = Field(ge=1)
    location_id: int = Field(ge=1)


class RoutingPreviewOut(BaseModel):
    handler: Optional[UserPublic] = None
    matched_rule_id: Optional[int] = None
    match_kind: str
