from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.enums import IssueStatus
from app.schemas.user import UserOut
from app.schemas.issue_type import IssueTypeOut
from app.schemas.location import LocationOut
from app.schemas.report import ReportOut
from app.schemas.escalation import EscalationOut
from app.schemas.resolution_evidence import ResolutionEvidenceOut
from app.schemas.verification import VerificationOut
from app.schemas.timeline import TimelineEventOut

class IssueBase(BaseModel):
    issue_type_id: int
    location_id: int
    specific_asset: Optional[str] = None
    title: str
    description: str
    requires_verification: bool = True

class IssueCreate(IssueBase):
    pass

class IssueOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    issue_type_id: int
    location_id: int
    specific_asset: Optional[str] = None
    title: str
    description: str
    status: IssueStatus
    current_handler_id: Optional[int] = None
    requires_verification: bool
    created_at: datetime
    updated_at: datetime
    report_count: int = 0
    current_handler: Optional[UserOut] = None
    issue_type: Optional[IssueTypeOut] = None
    location: Optional[LocationOut] = None

class IssueDetailOut(IssueOut):
    model_config = ConfigDict(from_attributes=True)
    reports: List[ReportOut] = []
    escalations: List[EscalationOut] = []
    evidences: List[ResolutionEvidenceOut] = []
    verifications: List[VerificationOut] = []
    timeline_events: List[TimelineEventOut] = []

class IssueReassignRequest(BaseModel):
    handler_id: int
    reason: Optional[str] = None

