from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import ReportStatus
from app.schemas.issue_type import IssueTypeOut
from app.schemas.location import LocationOut
from app.schemas.user import UserPublic
from app.schemas.validators import validate_attachment_url

DESCRIPTION_MIN = 10
DESCRIPTION_MAX = 2000
ASSET_MAX = 150


class ReportCreate(BaseModel):
    issue_type_id: int = Field(ge=1)
    location_id: int = Field(ge=1)
    specific_asset: Optional[str] = Field(default=None, max_length=ASSET_MAX)
    description: str = Field(min_length=DESCRIPTION_MIN, max_length=DESCRIPTION_MAX)
    photo_url: Optional[str] = None
    existing_issue_id: Optional[int] = Field(default=None, ge=1)

    @field_validator("description", "specific_asset")
    @classmethod
    def strip_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("photo_url")
    @classmethod
    def check_photo_url(cls, value: Optional[str]) -> Optional[str]:
        return validate_attachment_url(value)


class DuplicateCheckRequest(BaseModel):
    issue_type_id: int = Field(ge=1)
    location_id: int = Field(ge=1)
    specific_asset: Optional[str] = Field(default=None, max_length=ASSET_MAX)


class DuplicateIssueCandidate(BaseModel):
    issue_id: int
    title: str
    description: str
    status: str
    created_at: datetime
    affected_student_count: int
    report_count: int
    location_name: str
    issue_category: str
    issue_sub_type: str
    specific_asset: Optional[str] = None
    asset_match: bool
    already_reported_by_you: bool


class DuplicateCheckResponse(BaseModel):
    has_match: bool
    message: str
    candidates: List[DuplicateIssueCandidate] = []


class ReporterContact(BaseModel):
    """Attached to a report only for the staff member actually working the issue.
    Everyone else gets the display name or nothing at all."""

    model_config = ConfigDict(from_attributes=True)
    email: str
    phone: Optional[str] = None
    department: Optional[str] = None


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    issue_id: Optional[int] = None
    reporter_id: int
    issue_type_id: int
    location_id: int
    specific_asset: Optional[str] = None
    description: str
    photo_url: Optional[str] = None
    status: ReportStatus
    created_at: datetime
    reporter: Optional[UserPublic] = None
    reporter_contact: Optional[ReporterContact] = None
    issue_type: Optional[IssueTypeOut] = None
    location: Optional[LocationOut] = None
