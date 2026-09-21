from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import IssueStatus
from app.schemas.escalation import EscalationOut
from app.schemas.issue_type import IssueTypeOut
from app.schemas.location import LocationOut
from app.schemas.report import ReportOut
from app.schemas.resolution_evidence import ResolutionEvidenceOut
from app.schemas.timeline import TimelineEventOut
from app.schemas.user import UserPublic
from app.schemas.verification import VerificationOut

ItemT = TypeVar("ItemT")


class Page(BaseModel, Generic[ItemT]):
    items: List[ItemT]
    total: int
    limit: int
    offset: int


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
    needs_triage: bool = False
    affected_student_count: int = 0
    report_count: int = 0
    created_at: datetime
    updated_at: datetime
    current_handler: Optional[UserPublic] = None
    issue_type: Optional[IssueTypeOut] = None
    location: Optional[LocationOut] = None


class IssueDetailOut(IssueOut):
    model_config = ConfigDict(from_attributes=True)
    reports: List[ReportOut] = []
    escalations: List[EscalationOut] = []
    evidences: List[ResolutionEvidenceOut] = []
    verifications: List[VerificationOut] = []
    timeline_events: List[TimelineEventOut] = []
    viewer_is_affected: bool = False
    viewer_can_verify: bool = False


class IssueReassignRequest(BaseModel):
    handler_id: int = Field(ge=1)
    reason: Optional[str] = Field(default=None, max_length=1000)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        return value.strip() or None
