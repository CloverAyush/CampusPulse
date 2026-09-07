from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import VerificationStatus
from app.schemas.user import UserOut

class VerificationCreate(BaseModel):
    status: VerificationStatus
    comment: Optional[str] = None

class VerificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    issue_id: int
    verified_by_id: int
    status: VerificationStatus
    comment: Optional[str] = None
    created_at: datetime
    verified_by: Optional[UserOut] = None

