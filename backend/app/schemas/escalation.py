from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.user import UserPublic


class EscalationCreate(BaseModel):
    reason: str = Field(min_length=15, max_length=2000)
    escalated_to_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 15:
            raise ValueError("State why this is outside your authority in at least 15 characters")
        return cleaned


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
    escalated_by: Optional[UserPublic] = None
    escalated_to: Optional[UserPublic] = None
