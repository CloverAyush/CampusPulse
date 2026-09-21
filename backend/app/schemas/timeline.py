from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import IssueStatus, TimelineEventType
from app.schemas.user import UserPublic


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
    created_at: datetime
    actor: Optional[UserPublic] = None
