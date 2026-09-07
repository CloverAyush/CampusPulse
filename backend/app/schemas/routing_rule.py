from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.user import UserOut
from app.schemas.issue_type import IssueTypeOut
from app.schemas.location import LocationOut

class RoutingRuleBase(BaseModel):
    issue_type_id: Optional[int] = None
    location_id: Optional[int] = None
    handler_id: int
    priority: int = 10
    is_active: bool = True

class RoutingRuleCreate(RoutingRuleBase):
    pass

class RoutingRuleUpdate(BaseModel):
    issue_type_id: Optional[int] = None
    location_id: Optional[int] = None
    handler_id: Optional[int] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None

class RoutingRuleOut(RoutingRuleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    handler: Optional[UserOut] = None
    issue_type: Optional[IssueTypeOut] = None
    location: Optional[LocationOut] = None

