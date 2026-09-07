from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.enums import ReportStatus
from app.schemas.user import UserOut
from app.schemas.issue_type import IssueTypeOut
from app.schemas.location import LocationOut

class ReportCreate(BaseModel):
    issue_type_id: int
    location_id: int
    specific_asset: Optional[str] = None
    description: str
    photo_url: Optional[str] = None
    existing_issue_id: Optional[int] = None

class DuplicateCheckRequest(BaseModel):
    issue_type_id: int
    location_id: int
    specific_asset: Optional[str] = None

class DuplicateIssueCandidate(BaseModel):
    issue_id: int
    title: str
    description: str
    status: str
    created_at: datetime
    report_count: int
    location_name: str
    issue_category: str
    issue_sub_type: str
    specific_asset: Optional[str] = None

class DuplicateCheckResponse(BaseModel):
    has_match: bool
    message: str
    candidates: list[DuplicateIssueCandidate] = []

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
    reporter: Optional[UserOut] = None
    issue_type: Optional[IssueTypeOut] = None
    location: Optional[LocationOut] = None

