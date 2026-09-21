from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import EvidenceType
from app.schemas.user import UserPublic
from app.schemas.validators import validate_attachment_url


class ResolutionEvidenceCreate(BaseModel):
    evidence_type: EvidenceType = EvidenceType.DESCRIPTION
    notes: str = Field(min_length=10, max_length=2000)
    attachment_url: Optional[str] = None

    @field_validator("notes")
    @classmethod
    def strip_notes(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 10:
            raise ValueError("Describe what was actually done in at least 10 characters")
        return cleaned

    @field_validator("attachment_url")
    @classmethod
    def check_attachment(cls, value: Optional[str]) -> Optional[str]:
        return validate_attachment_url(value)


class ResolutionEvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    issue_id: int
    submitted_by_id: int
    evidence_type: EvidenceType
    notes: str
    attachment_url: Optional[str] = None
    resolution_round: int
    created_at: datetime
    submitted_by: Optional[UserPublic] = None
