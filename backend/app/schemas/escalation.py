from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.schemas.user import UserOut

class EscalationCreate(BaseModel):
    reason: str
    escalated_to_id: Optional[int] = None

class EscalationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    issue_id: int
    escalated_by_id: int
    escalated_to_id: Optional[int] = None
    reason: str
    previous_status: str
    history_snapshot: Optional[str] = None
    created_at: datetime
    escalated_by: Optional[UserOut] = None
    escalated_to: Optional[UserOut] = None

