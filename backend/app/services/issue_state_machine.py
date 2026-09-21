import json
import logging
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.errors import (
    ConflictError,
    InvalidTransitionError,
    NotFoundError,
    PermissionDeniedError,
    ValidationError,
)
from app.models.enums import (
    EvidenceType,
    IssueStatus,
    ReportStatus,
    TimelineEventType,
    UserRole,
    VerificationStatus,
)
from app.models.escalation import Escalation
from app.models.issue import Issue
from app.models.issue_type import IssueType
from app.models.location import Location
from app.models.report import Report
from app.models.resolution_evidence import ResolutionEvidence
from app.models.timeline import TimelineEvent
from app.models.user import User
from app.models.verification import Verification
from app.services.notification_service import notify_affected_students, notify_user
from app.services.routing import find_admins, resolve_handler

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = (
    IssueStatus.OPEN,
    IssueStatus.IN_PROGRESS,
    IssueStatus.ESCALATED,
    IssueStatus.REOPENED,
    IssueStatus.RESOLVED_PENDING_VERIFICATION,
)

# The complete set of legal moves. Every transition in this module is checked against
# this table, so an illegal move fails the same way regardless of which caller tried it.
ALLOWED_TRANSITIONS: Dict[IssueStatus, set] = {
    IssueStatus.OPEN: {IssueStatus.IN_PROGRESS, IssueStatus.ESCALATED,
                       IssueStatus.RESOLVED_PENDING_VERIFICATION, IssueStatus.VERIFIED_CLOSED},
    IssueStatus.IN_PROGRESS: {IssueStatus.ESCALATED, IssueStatus.RESOLVED_PENDING_VERIFICATION,
                              IssueStatus.VERIFIED_CLOSED},
    IssueStatus.REOPENED: {IssueStatus.IN_PROGRESS, IssueStatus.ESCALATED,
                           IssueStatus.RESOLVED_PENDING_VERIFICATION, IssueStatus.VERIFIED_CLOSED},
    IssueStatus.ESCALATED: {IssueStatus.IN_PROGRESS, IssueStatus.RESOLVED_PENDING_VERIFICATION,
                            IssueStatus.VERIFIED_CLOSED},
    IssueStatus.RESOLVED_PENDING_VERIFICATION: {IssueStatus.VERIFIED_CLOSED, IssueStatus.REOPENED},
    IssueStatus.VERIFIED_CLOSED: set(),
}


def _assert_transition(issue: Issue, target: IssueStatus, action: str) -> None:
    if target not in ALLOWED_TRANSITIONS[issue.status]:
        raise InvalidTransitionError(
            f"Cannot {action} an issue that is currently {issue.status.value.replace('_', ' ').lower()}."
        )


def _lock_issue(db: Session, issue_id: int) -> Issue:
    """Serialise concurrent handler actions on one issue. SQLite has a single writer
    so its transaction already provides this; other backends need an explicit lock."""
    query = db.query(Issue).filter(Issue.id == issue_id)
    if not settings.is_sqlite:
        query = query.with_for_update()

    issue = query.first()
    if not issue:
        raise NotFoundError("Issue not found")
    return issue


def _current_resolution_round(db: Session, issue_id: int) -> int:
    rounds = db.query(func.max(ResolutionEvidence.resolution_round)).filter(
        ResolutionEvidence.issue_id == issue_id
    ).scalar()
    return int(rounds or 0)


def count_affected_students(db: Session, issue_id: int) -> int:
    """The number of distinct people affected, which is the signal the institution
    acts on. Counting rows instead would let one impatient student inflate it."""
    return int(
        db.query(func.count(func.distinct(Report.reporter_id)))
        .filter(Report.issue_id == issue_id)
        .scalar()
        or 0
    )


def count_reports(db: Session, issue_id: int) -> int:
    return int(db.query(func.count(Report.id)).filter(Report.issue_id == issue_id).scalar() or 0)


def create_timeline_event(
    db: Session,
    issue_id: int,
    event_type: TimelineEventType,
    title: str,
    actor_id: Optional[int] = None,
    from_status: Optional[IssueStatus] = None,
    to_status: Optional[IssueStatus] = None,
    details: Optional[str] = None,
    metadata_dict: Optional[Dict[str, Any]] = None,
) -> TimelineEvent:
    event = TimelineEvent(
        issue_id=issue_id,
        actor_id=actor_id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        title=title,
        details=details,
        metadata_json=json.dumps(metadata_dict) if metadata_dict else None,
    )
    db.add(event)
    return event


def _load_taxonomy(db: Session, issue_type_id: int, location_id: int) -> Tuple[IssueType, Location]:
    issue_type = db.query(IssueType).filter(
        IssueType.id == issue_type_id, IssueType.is_active.is_(True)
    ).first()
    if not issue_type:
        raise NotFoundError("That issue type is not available")

    location = db.query(Location).filter(
        Location.id == location_id, Location.is_active.is_(True)
    ).first()
    if not location:
        raise NotFoundError("That location is not available")

    return issue_type, location


def create_issue_and_route_report(
    db: Session,
    reporter: User,
    issue_type_id: int,
    location_id: int,
    description: str,
    specific_asset: Optional[str] = None,
    photo_url: Optional[str] = None,
) -> Tuple[Issue, Report]:
    issue_type, location = _load_taxonomy(db, issue_type_id, location_id)
    routing = resolve_handler(db, issue_type_id, location_id)

    asset_suffix = f" ({specific_asset})" if specific_asset else ""
    title = f"{issue_type.category} - {issue_type.sub_type}{asset_suffix} at {location.name}"

    issue = Issue(
        issue_type_id=issue_type_id,
        location_id=location_id,
        specific_asset=specific_asset,
        title=title,
        description=description,
        status=IssueStatus.OPEN,
        current_handler_id=routing.handler.id if routing.handler else None,
        requires_verification=issue_type.requires_verification,
        needs_triage=routing.handler is None,
        affected_student_count=1,
    )
    db.add(issue)
    db.flush()

    report = Report(
        issue_id=issue.id,
        reporter_id=reporter.id,
        issue_type_id=issue_type_id,
        location_id=location_id,
        specific_asset=specific_asset,
        description=description,
        photo_url=photo_url,
        status=ReportStatus.LINKED_TO_ISSUE,
    )
    db.add(report)
    db.flush()

    create_timeline_event(
        db,
        issue_id=issue.id,
        actor_id=reporter.id,
        event_type=TimelineEventType.REPORT_SUBMITTED,
        to_status=IssueStatus.OPEN,
        title=f"Reported by {reporter.full_name}",
        details=description,
        metadata_dict={"report_id": report.id},
    )

    if routing.handler:
        create_timeline_event(
            db,
            issue_id=issue.id,
            event_type=TimelineEventType.ROUTED,
            to_status=IssueStatus.OPEN,
            title=f"Routed to {routing.handler.full_name}",
            details=(
                f"Matched routing rule ({routing.match_kind}) for "
                f"{issue_type.category} / {issue_type.sub_type} at {location.name}."
            ),
            metadata_dict={"rule_id": routing.rule.id if routing.rule else None,
                           "match_kind": routing.match_kind},
        )
        notify_user(
            db,
            user_id=routing.handler.id,
            title="New issue assigned",
            message=f"'{title}' has been routed to you.",
            issue_id=issue.id,
        )
    else:
        create_timeline_event(
            db,
            issue_id=issue.id,
            event_type=TimelineEventType.ROUTED,
            to_status=IssueStatus.OPEN,
            title="Awaiting triage",
            details="No routing rule matched and no catch-all handler is configured. Administrators have been notified.",
            metadata_dict={"match_kind": routing.match_kind},
        )
        admins = find_admins(db)
        for admin in admins:
            notify_user(
                db,
                user_id=admin.id,
                title="Issue needs triage",
                message=f"'{title}' could not be routed automatically. Assign a handler.",
                issue_id=issue.id,
            )
        logger.error(
            "Issue created without a handler",
            extra={"issue_id": issue.id, "admins_notified": len(admins)},
        )

    db.commit()
    db.refresh(issue)
    db.refresh(report)

    logger.info(
        "Issue created",
        extra={"issue_id": issue.id, "report_id": report.id,
               "handler_id": issue.current_handler_id, "match_kind": routing.match_kind},
    )
    return issue, report


def link_report_to_existing_issue(
    db: Session,
    reporter: User,
    existing_issue_id: int,
    issue_type_id: int,
    location_id: int,
    description: str,
    specific_asset: Optional[str] = None,
    photo_url: Optional[str] = None,
) -> Tuple[Issue, Report]:
    """Joining an existing issue is only legitimate when it is genuinely the same
    problem, so the structured fields must match and the issue must still be open."""
    _load_taxonomy(db, issue_type_id, location_id)
    issue = _lock_issue(db, existing_issue_id)

    if issue.status not in ACTIVE_STATUSES:
        raise InvalidTransitionError(
            "That issue has already been closed. Submit this as a new report instead."
        )

    if issue.issue_type_id != issue_type_id or issue.location_id != location_id:
        raise ValidationError(
            "This report does not match the issue you are joining. "
            "Submit it as a separate problem instead."
        )

    already_reported = (
        db.query(Report.id)
        .filter(Report.issue_id == issue.id, Report.reporter_id == reporter.id)
        .first()
    )
    if already_reported:
        raise ConflictError("You have already reported this issue.")

    report = Report(
        issue_id=issue.id,
        reporter_id=reporter.id,
        issue_type_id=issue_type_id,
        location_id=location_id,
        specific_asset=specific_asset,
        description=description,
        photo_url=photo_url,
        status=ReportStatus.LINKED_TO_ISSUE,
    )
    db.add(report)
    db.flush()

    issue.affected_student_count = count_affected_students(db, issue.id)

    create_timeline_event(
        db,
        issue_id=issue.id,
        actor_id=reporter.id,
        event_type=TimelineEventType.REPORT_LINKED,
        title=f"Also reported by {reporter.full_name}",
        details=description,
        metadata_dict={"report_id": report.id,
                       "affected_student_count": issue.affected_student_count},
    )

    if issue.current_handler_id:
        notify_user(
            db,
            user_id=issue.current_handler_id,
            title="Another student reported this issue",
            message=(
                f"'{issue.title}' now affects {issue.affected_student_count} students."
            ),
            issue_id=issue.id,
        )

    db.commit()
    db.refresh(issue)
    db.refresh(report)

    logger.info(
        "Report linked to existing issue",
        extra={"issue_id": issue.id, "report_id": report.id,
               "affected_student_count": issue.affected_student_count},
    )
    return issue, report


def start_issue_progress(db: Session, issue_id: int, current_user: User) -> Issue:
    issue = _lock_issue(db, issue_id)

    is_assigned = issue.current_handler_id == current_user.id
    is_privileged = current_user.role in (UserRole.ADMIN, UserRole.HIGHER_AUTHORITY)
    if not (is_assigned or is_privileged):
        raise PermissionDeniedError("Only the assigned handler can update this issue")

    _assert_transition(issue, IssueStatus.IN_PROGRESS, "start work on")

    previous_status = issue.status
    issue.status = IssueStatus.IN_PROGRESS

    create_timeline_event(
        db,
        issue_id=issue.id,
        actor_id=current_user.id,
        event_type=TimelineEventType.STARTED_PROGRESS,
        from_status=previous_status,
        to_status=IssueStatus.IN_PROGRESS,
        title=f"Work started by {current_user.full_name}",
    )

    notify_affected_students(
        db,
        issue_id=issue.id,
        title="Issue in progress",
        message=f"Work has started on '{issue.title}'.",
    )

    db.commit()
    db.refresh(issue)
    logger.info("Issue moved to in progress", extra={"issue_id": issue.id, "actor_id": current_user.id})
    return issue


def escalate_issue(
    db: Session,
    issue_id: int,
    escalating_user: User,
    reason: str,
    escalated_to_id: Optional[int] = None,
) -> Escalation:
    issue = _lock_issue(db, issue_id)

    is_assigned = issue.current_handler_id == escalating_user.id
    if not (is_assigned or escalating_user.role == UserRole.ADMIN):
        raise PermissionDeniedError("Only the assigned handler can escalate this issue")

    _assert_transition(issue, IssueStatus.ESCALATED, "escalate")

    if escalated_to_id is not None:
        authority = db.query(User).filter(
            User.id == escalated_to_id,
            User.is_active.is_(True),
            User.role.in_([UserRole.HIGHER_AUTHORITY, UserRole.ADMIN]),
        ).first()
        if not authority:
            raise NotFoundError("That escalation target is not available")
    else:
        authority = db.query(User).filter(
            User.role == UserRole.HIGHER_AUTHORITY, User.is_active.is_(True)
        ).order_by(User.id).first()
        if not authority:
            authority = db.query(User).filter(
                User.role == UserRole.ADMIN, User.is_active.is_(True)
            ).order_by(User.id).first()
        if not authority:
            raise ConflictError(
                "No higher authority is configured to receive escalations. Contact an administrator."
            )

    snapshot = {
        "issue_id": issue.id,
        "title": issue.title,
        "status_at_escalation": issue.status.value,
        "location": issue.location.name if issue.location else None,
        "category": issue.issue_type.category if issue.issue_type else None,
        "sub_type": issue.issue_type.sub_type if issue.issue_type else None,
        "specific_asset": issue.specific_asset,
        "affected_student_count": count_affected_students(db, issue.id),
        "reports": [
            {"id": r.id, "reporter": r.reporter.full_name, "description": r.description,
             "photo_url": r.photo_url, "created_at": r.created_at.isoformat()}
            for r in issue.reports
        ],
        "evidence": [
            {"id": e.id, "type": e.evidence_type.value, "notes": e.notes,
             "attachment_url": e.attachment_url, "submitted_by": e.submitted_by.full_name,
             "created_at": e.created_at.isoformat()}
            for e in issue.evidences
        ],
        "timeline": [
            {"type": t.event_type.value, "title": t.title, "details": t.details,
             "actor": t.actor.full_name if t.actor else "System",
             "created_at": t.created_at.isoformat()}
            for t in issue.timeline_events
        ],
    }

    previous_status = issue.status
    issue.status = IssueStatus.ESCALATED

    escalation = Escalation(
        issue_id=issue.id,
        escalated_by_id=escalating_user.id,
        escalated_to_id=authority.id,
        reason=reason,
        previous_status=previous_status.value,
        history_snapshot=json.dumps(snapshot),
    )
    db.add(escalation)
    db.flush()

    create_timeline_event(
        db,
        issue_id=issue.id,
        actor_id=escalating_user.id,
        event_type=TimelineEventType.ESCALATED,
        from_status=previous_status,
        to_status=IssueStatus.ESCALATED,
        title=f"Escalated by {escalating_user.full_name}",
        details=reason,
        metadata_dict={"escalation_id": escalation.id, "escalated_to_id": authority.id},
    )

    notify_user(
        db,
        user_id=authority.id,
        title="Issue escalated to you",
        message=f"{escalating_user.full_name} escalated '{issue.title}': {reason}",
        issue_id=issue.id,
    )
    notify_affected_students(
        db,
        issue_id=issue.id,
        title="Issue escalated",
        message=f"'{issue.title}' has been escalated to a higher authority.",
    )

    db.commit()
    db.refresh(escalation)
    logger.info(
        "Issue escalated",
        extra={"issue_id": issue.id, "escalated_by": escalating_user.id, "escalated_to": authority.id},
    )
    return escalation


def resolve_issue_with_evidence(
    db: Session,
    issue_id: int,
    resolving_user: User,
    evidence_type: EvidenceType,
    notes: str,
    attachment_url: Optional[str] = None,
) -> ResolutionEvidence:
    issue = _lock_issue(db, issue_id)

    is_assigned = issue.current_handler_id == resolving_user.id
    is_privileged = resolving_user.role in (UserRole.ADMIN, UserRole.HIGHER_AUTHORITY)
    if not (is_assigned or is_privileged):
        raise PermissionDeniedError("Only the assigned handler can resolve this issue")

    target_status = (
        IssueStatus.RESOLVED_PENDING_VERIFICATION
        if issue.requires_verification
        else IssueStatus.VERIFIED_CLOSED
    )
    _assert_transition(issue, target_status, "resolve")

    previous_status = issue.status
    issue.status = target_status
    resolution_round = _current_resolution_round(db, issue.id) + 1

    evidence = ResolutionEvidence(
        issue_id=issue.id,
        submitted_by_id=resolving_user.id,
        evidence_type=evidence_type,
        notes=notes,
        attachment_url=attachment_url,
        resolution_round=resolution_round,
    )
    db.add(evidence)
    db.flush()

    awaiting = target_status == IssueStatus.RESOLVED_PENDING_VERIFICATION
    create_timeline_event(
        db,
        issue_id=issue.id,
        actor_id=resolving_user.id,
        event_type=TimelineEventType.RESOLVED,
        from_status=previous_status,
        to_status=target_status,
        title=(
            f"Resolved by {resolving_user.full_name}"
            + (" - awaiting student verification" if awaiting else " and closed")
        ),
        details=notes,
        metadata_dict={"evidence_id": evidence.id, "evidence_type": evidence_type.value,
                       "resolution_round": resolution_round},
    )

    notify_affected_students(
        db,
        issue_id=issue.id,
        title="Issue resolved" if not awaiting else "Please confirm this is fixed",
        message=(
            f"'{issue.title}' has been marked resolved. Confirm it is actually fixed, "
            "or tell us it is not."
            if awaiting
            else f"'{issue.title}' has been resolved and closed."
        ),
    )

    db.commit()
    db.refresh(evidence)
    logger.info(
        "Issue resolved",
        extra={"issue_id": issue.id, "actor_id": resolving_user.id,
               "resolution_round": resolution_round, "awaiting_verification": awaiting},
    )
    return evidence


def verify_issue_resolution(
    db: Session,
    issue_id: int,
    verifying_user: User,
    verification_status: VerificationStatus,
    comment: Optional[str] = None,
) -> Verification:
    """The first affected student to respond settles it: confirming closes the issue,
    disputing reopens it. That is a deliberate product choice, recorded here so the
    behaviour is obvious to the next reader."""
    issue = _lock_issue(db, issue_id)

    if issue.status != IssueStatus.RESOLVED_PENDING_VERIFICATION:
        raise InvalidTransitionError(
            f"This issue is not awaiting verification (it is {issue.status.value.replace('_', ' ').lower()})."
        )

    is_reporter = (
        db.query(Report.id)
        .filter(Report.issue_id == issue.id, Report.reporter_id == verifying_user.id)
        .first()
        is not None
    )
    if not is_reporter and verifying_user.role != UserRole.ADMIN:
        raise PermissionDeniedError(
            "Only students affected by this issue can verify its resolution"
        )

    resolution_round = _current_resolution_round(db, issue.id)
    duplicate = (
        db.query(Verification.id)
        .filter(
            Verification.issue_id == issue.id,
            Verification.verified_by_id == verifying_user.id,
            Verification.resolution_round == resolution_round,
        )
        .first()
    )
    if duplicate:
        raise ConflictError("You have already responded to this resolution.")

    confirmed = verification_status == VerificationStatus.CONFIRMED
    target_status = IssueStatus.VERIFIED_CLOSED if confirmed else IssueStatus.REOPENED
    _assert_transition(issue, target_status, "verify")

    verification = Verification(
        issue_id=issue.id,
        verified_by_id=verifying_user.id,
        status=verification_status,
        comment=comment,
        resolution_round=resolution_round,
    )
    db.add(verification)
    db.flush()

    previous_status = issue.status
    issue.status = target_status

    create_timeline_event(
        db,
        issue_id=issue.id,
        actor_id=verifying_user.id,
        event_type=TimelineEventType.VERIFIED if confirmed else TimelineEventType.DISPUTED,
        from_status=previous_status,
        to_status=target_status,
        title=(
            f"Confirmed fixed by {verifying_user.full_name}"
            if confirmed
            else f"Reopened by {verifying_user.full_name} - still not fixed"
        ),
        details=comment,
        metadata_dict={"resolution_round": resolution_round},
    )

    if issue.current_handler_id:
        notify_user(
            db,
            user_id=issue.current_handler_id,
            title="Resolution confirmed" if confirmed else "Issue reopened",
            message=(
                f"{verifying_user.full_name} confirmed '{issue.title}' is fixed."
                if confirmed
                else f"{verifying_user.full_name} says '{issue.title}' is still not fixed."
                + (f" Comment: {comment}" if comment else "")
            ),
            issue_id=issue.id,
        )

    notify_affected_students(
        db,
        issue_id=issue.id,
        title="Issue closed" if confirmed else "Issue reopened",
        message=(
            f"'{issue.title}' was confirmed fixed and is now closed."
            if confirmed
            else f"'{issue.title}' was reported as still broken and has been reopened."
        ),
        exclude_user_id=verifying_user.id,
    )

    db.commit()
    db.refresh(verification)
    logger.info(
        "Resolution verification recorded",
        extra={"issue_id": issue.id, "actor_id": verifying_user.id,
               "verification_status": verification_status.value},
    )
    return verification


def reassign_issue_handler(
    db: Session,
    issue_id: int,
    new_handler_id: int,
    reassigned_by: User,
    reason: Optional[str] = None,
) -> Issue:
    if reassigned_by.role not in (UserRole.ADMIN, UserRole.HIGHER_AUTHORITY):
        raise PermissionDeniedError("Only an admin or higher authority can reassign issues")

    issue = _lock_issue(db, issue_id)

    if issue.status == IssueStatus.VERIFIED_CLOSED:
        raise InvalidTransitionError("A closed issue cannot be reassigned")

    new_handler = db.query(User).filter(
        User.id == new_handler_id,
        User.is_active.is_(True),
        User.role.in_([UserRole.HANDLER, UserRole.HIGHER_AUTHORITY, UserRole.ADMIN]),
    ).first()
    if not new_handler:
        raise NotFoundError("That handler is not available")

    if issue.current_handler_id == new_handler.id:
        raise ConflictError("That handler is already assigned to this issue")

    previous_handler_name = issue.current_handler.full_name if issue.current_handler else "nobody"
    previous_status = issue.status

    issue.current_handler_id = new_handler.id
    issue.needs_triage = False
    if issue.status == IssueStatus.ESCALATED:
        issue.status = IssueStatus.IN_PROGRESS

    create_timeline_event(
        db,
        issue_id=issue.id,
        actor_id=reassigned_by.id,
        event_type=TimelineEventType.REASSIGNED,
        from_status=previous_status,
        to_status=issue.status,
        title=f"Reassigned to {new_handler.full_name} by {reassigned_by.full_name}",
        details=f"Previously assigned to {previous_handler_name}."
        + (f" Reason: {reason}" if reason else ""),
    )

    notify_user(
        db,
        user_id=new_handler.id,
        title="Issue assigned to you",
        message=f"'{issue.title}' was assigned to you by {reassigned_by.full_name}.",
        issue_id=issue.id,
    )

    db.commit()
    db.refresh(issue)
    logger.info(
        "Issue reassigned",
        extra={"issue_id": issue.id, "new_handler_id": new_handler.id, "actor_id": reassigned_by.id},
    )
    return issue
