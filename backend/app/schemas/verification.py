from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import VerificationStatus
from app.schemas.user import UserPublic


class VerificationCreate(BaseModel):
    status: VerificationStatus
    comment: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("comment")
    @classmethod
    def strip_comment(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip() or None


class VerificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    issue_id: int
    verified_by_id: int
    status: VerificationStatus
    comment: Optional[str] = None
    resolution_round: int
    created_at: datetime
    verified_by: Optional[UserPublic] = None
