from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import TimelineEventType, IssueStatus
from app.schemas.user import UserOut

class TimelineEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    issue_id: int
    actor_id: Optional[int] = None
    event_type: TimelineEventType
    from_status: Optional[IssueStatus] = None
    to_status: Optional[IssueStatus] = None
    title: str
    details: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: datetime
    actor: Optional[UserOut] = None

