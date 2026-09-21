import logging
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import (
    can_see_contact_details,
    get_current_user,
    is_affected_reporter,
    parse_pagination,
)
from app.config import settings
from app.database import get_db
from app.errors import NotFoundError, PermissionDeniedError, ValidationError
from app.models.enums import IssueStatus, UserRole
from app.models.issue import Issue
from app.models.report import Report
from app.models.user import User
from app.rate_limit import rate_limit
from app.schemas.escalation import EscalationCreate, EscalationOut
from app.schemas.issue import IssueDetailOut, IssueOut, IssueReassignRequest, Page
from app.schemas.report import ReporterContact, ReportOut
from app.schemas.resolution_evidence import ResolutionEvidenceCreate, ResolutionEvidenceOut
from app.schemas.timeline import TimelineEventOut
from app.schemas.user import UserPublic
from app.schemas.verification import VerificationCreate, VerificationOut
from app.services.issue_state_machine import (
    count_affected_students,
    escalate_issue,
    reassign_issue_handler,
    resolve_issue_with_evidence,
    start_issue_progress,
    verify_issue_resolution,
)

logger = logging.getLogger(__name__)
router = APIRouter()

action_rate_limit = rate_limit("issue_action", settings.WRITE_RATE_LIMIT_PER_MINUTE, 60)

SCOPE_MINE = "mine"
SCOPE_ALL = "all"
SCOPE_ASSIGNED = "assigned"
SCOPE_ESCALATED = "escalated"
SCOPE_TRIAGE = "triage"
VALID_SCOPES = {SCOPE_MINE, SCOPE_ALL, SCOPE_ASSIGNED, SCOPE_ESCALATED, SCOPE_TRIAGE}

ANONYMOUS_REPORTER_LABEL = "A student"


def _counts_for(db: Session, issue_ids: List[int]) -> tuple[Dict[int, int], Dict[int, int]]:
    if not issue_ids:
        return {}, {}

    reports = dict(
        db.query(Report.issue_id, func.count(Report.id))
        .filter(Report.issue_id.in_(issue_ids))
        .group_by(Report.issue_id)
        .all()
    )
    affected = dict(
        db.query(Report.issue_id, func.count(func.distinct(Report.reporter_id)))
        .filter(Report.issue_id.in_(issue_ids))
        .group_by(Report.issue_id)
        .all()
    )
    return reports, affected


def _default_scope(user: User) -> str:
    if user.role == UserRole.STUDENT:
        return SCOPE_MINE
    if user.role == UserRole.HANDLER:
        return SCOPE_ASSIGNED
    if user.role == UserRole.HIGHER_AUTHORITY:
        return SCOPE_ESCALATED
    return SCOPE_ALL


def _apply_scope(query, db: Session, user: User, scope: str):
    if scope == SCOPE_MINE:
        reported = select(Report.issue_id).where(Report.reporter_id == user.id)
        return query.filter(Issue.id.in_(reported))

    if scope == SCOPE_ASSIGNED:
        if user.role == UserRole.STUDENT:
            raise PermissionDeniedError("Students do not have assigned issues")
        return query.filter(Issue.current_handler_id == user.id)

    if scope == SCOPE_ESCALATED:
        if user.role == UserRole.STUDENT:
            raise PermissionDeniedError("Only staff can browse the escalation queue")
        return query.filter(Issue.status == IssueStatus.ESCALATED)

    if scope == SCOPE_TRIAGE:
        if user.role != UserRole.ADMIN:
            raise PermissionDeniedError("Only administrators can view the triage queue")
        return query.filter(Issue.needs_triage.is_(True))

    return query


@router.get("", response_model=Page[IssueOut])
def list_issues(
    scope: Optional[str] = Query(default=None, description="mine | all | assigned | escalated | triage"),
    status_filter: Optional[IssueStatus] = Query(default=None, alias="status"),
    search: Optional[str] = Query(default=None, max_length=100),
    limit: Optional[int] = Query(default=None),
    offset: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scope decides whose issues are returned. Students get 'mine' by default and
    can switch to 'all' to browse the campus board; staff scopes are role-gated."""
    resolved_scope = scope or _default_scope(current_user)
    if resolved_scope not in VALID_SCOPES:
        raise ValidationError(f"scope must be one of: {', '.join(sorted(VALID_SCOPES))}")

    resolved_limit, resolved_offset = parse_pagination(limit, offset)

    query = _apply_scope(db.query(Issue), db, current_user, resolved_scope)

    if status_filter:
        query = query.filter(Issue.status == status_filter)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(Issue.title.ilike(pattern))

    total = query.count()
    issues = (
        query.options(
            joinedload(Issue.issue_type),
            joinedload(Issue.location),
            joinedload(Issue.current_handler),
        )
        .order_by(desc(Issue.updated_at), desc(Issue.id))
        .limit(resolved_limit)
        .offset(resolved_offset)
        .all()
    )

    report_counts, affected_counts = _counts_for(db, [issue.id for issue in issues])

    items = []
    for issue in issues:
        item = IssueOut.model_validate(issue)
        item.report_count = report_counts.get(issue.id, 0)
        item.affected_student_count = affected_counts.get(issue.id, 0)
        items.append(item)

    return Page[IssueOut](items=items, total=total, limit=resolved_limit, offset=resolved_offset)


def _load_issue(db: Session, issue_id: int) -> Issue:
    issue = (
        db.query(Issue)
        .options(
            joinedload(Issue.issue_type),
            joinedload(Issue.location),
            joinedload(Issue.current_handler),
            joinedload(Issue.reports).joinedload(Report.reporter),
        )
        .filter(Issue.id == issue_id)
        .first()
    )
    if not issue:
        raise NotFoundError("Issue not found")
    return issue


def _build_detail(db: Session, issue: Issue, viewer: User) -> IssueDetailOut:
    viewer_is_affected = is_affected_reporter(db, issue.id, viewer.id)
    is_staff = viewer.role in (UserRole.HANDLER, UserRole.HIGHER_AUTHORITY, UserRole.ADMIN)
    show_contacts = can_see_contact_details(viewer, issue)

    detail = IssueDetailOut.model_validate(issue)
    detail.report_count = len(issue.reports)
    detail.affected_student_count = count_affected_students(db, issue.id)
    detail.viewer_is_affected = viewer_is_affected
    detail.viewer_can_verify = (
        viewer_is_affected and issue.status == IssueStatus.RESOLVED_PENDING_VERIFICATION
    )

    if show_contacts:
        detail.reports = [
            ReportOut.model_validate(report).model_copy(
                update={"reporter_contact": ReporterContact.model_validate(report.reporter)}
            )
            for report in issue.reports
        ]
    elif is_staff or viewer_is_affected:
        detail.reports = [ReportOut.model_validate(report) for report in issue.reports]
    else:
        # A student browsing the campus board sees that other people are affected and
        # what they said, but not who said it.
        detail.reports = [
            ReportOut.model_validate(report).model_copy(update={"reporter": None})
            for report in issue.reports
        ]
        detail.timeline_events = [_mask_student_event(event) for event in detail.timeline_events]

    return detail


def _mask_student_event(event: TimelineEventOut) -> TimelineEventOut:
    """Timeline titles are written as 'Reported by <name>', so masking the actor
    object alone would still leak the name in the text beside it."""
    actor = event.actor
    if actor is None or actor.role != UserRole.STUDENT:
        return event

    updates = {
        "actor": actor.model_copy(update={"full_name": ANONYMOUS_REPORTER_LABEL}),
        "title": event.title.replace(actor.full_name, ANONYMOUS_REPORTER_LABEL),
    }
    if event.details:
        updates["details"] = event.details.replace(actor.full_name, ANONYMOUS_REPORTER_LABEL)

    return event.model_copy(update=updates)


@router.get("/{issue_id}", response_model=IssueDetailOut)
def get_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = _load_issue(db, issue_id)
    return _build_detail(db, issue, current_user)


@router.get("/{issue_id}/history", response_model=List[TimelineEventOut])
def get_issue_history(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    issue = _load_issue(db, issue_id)
    events = [TimelineEventOut.model_validate(event) for event in issue.timeline_events]

    is_staff = current_user.role in (UserRole.HANDLER, UserRole.HIGHER_AUTHORITY, UserRole.ADMIN)
    if is_staff or is_affected_reporter(db, issue.id, current_user.id):
        return events

    return [_mask_student_event(event) for event in events]


@router.post("/{issue_id}/progress", response_model=IssueDetailOut,
             dependencies=[Depends(action_rate_limit)])
def mark_in_progress(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    start_issue_progress(db=db, issue_id=issue_id, current_user=current_user)
    return _build_detail(db, _load_issue(db, issue_id), current_user)


@router.post("/{issue_id}/resolve", response_model=ResolutionEvidenceOut,
             dependencies=[Depends(action_rate_limit)])
def resolve_issue(
    issue_id: int,
    evidence_in: ResolutionEvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return resolve_issue_with_evidence(
        db=db,
        issue_id=issue_id,
        resolving_user=current_user,
        evidence_type=evidence_in.evidence_type,
        notes=evidence_in.notes,
        attachment_url=evidence_in.attachment_url,
    )


@router.post("/{issue_id}/escalate", response_model=EscalationOut,
             dependencies=[Depends(action_rate_limit)])
def escalate(
    issue_id: int,
    escalation_in: EscalationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return escalate_issue(
        db=db,
        issue_id=issue_id,
        escalating_user=current_user,
        reason=escalation_in.reason,
        escalated_to_id=escalation_in.escalated_to_id,
    )


@router.get("/{issue_id}/escalation-targets", response_model=List[UserPublic])
def list_escalation_targets(
    issue_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """The handler escalation form needs the list of authorities. Scoped to this
    endpoint so handlers never have to call the admin user directory."""
    issue = _load_issue(db, issue_id)
    is_assigned = issue.current_handler_id == current_user.id
    if not (is_assigned or current_user.role in (UserRole.ADMIN, UserRole.HIGHER_AUTHORITY)):
        raise PermissionDeniedError("Only the assigned handler can escalate this issue")

    return (
        db.query(User)
        .filter(User.is_active.is_(True), User.role == UserRole.HIGHER_AUTHORITY)
        .order_by(User.full_name)
        .all()
    )


@router.post("/{issue_id}/verify", response_model=VerificationOut,
             dependencies=[Depends(action_rate_limit)])
def verify_issue(
    issue_id: int,
    verification_in: VerificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return verify_issue_resolution(
        db=db,
        issue_id=issue_id,
        verifying_user=current_user,
        verification_status=verification_in.status,
        comment=verification_in.comment,
    )


@router.post("/{issue_id}/reassign", response_model=IssueDetailOut,
             dependencies=[Depends(action_rate_limit)])
def reassign_issue(
    issue_id: int,
    payload: IssueReassignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reassign_issue_handler(
        db=db,
        issue_id=issue_id,
        new_handler_id=payload.handler_id,
        reassigned_by=current_user,
        reason=payload.reason,
    )
    return _build_detail(db, _load_issue(db, issue_id), current_user)
