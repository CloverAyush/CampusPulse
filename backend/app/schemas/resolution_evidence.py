from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import EvidenceType
from app.schemas.user import UserOut

class ResolutionEvidenceCreate(BaseModel):
    evidence_type: EvidenceType = EvidenceType.DESCRIPTION
    notes: str
    attachment_url: Optional[str] = None

class ResolutionEvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    issue_id: int
    submitted_by_id: int
    evidence_type: EvidenceType
    notes: str
    attachment_url: Optional[str] = None
    created_at: datetime
    submitted_by: Optional[UserOut] = None

