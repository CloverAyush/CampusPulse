import json
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.enums import (
    IssueStatus,
    ReportStatus,
    TimelineEventType,
    EvidenceType,
    VerificationStatus,
    UserRole
)
from app.models.user import User
from app.models.issue import Issue
from app.models.report import Report
from app.models.issue_type import IssueType
from app.models.location import Location
from app.models.escalation import Escalation
from app.models.resolution_evidence import ResolutionEvidence
from app.models.verification import Verification
from app.models.timeline import TimelineEvent
from app.services.routing import resolve_handler_deterministically
from app.services.notification_service import notify_user, notify_affected_students

def create_timeline_event(
    db: Session,
    issue_id: int,
    event_type: TimelineEventType,
    title: str,
    actor_id: Optional[int] = None,
    from_status: Optional[IssueStatus] = None,
    to_status: Optional[IssueStatus] = None,
    details: Optional[str] = None,
    metadata_dict: Optional[Dict[str, Any]] = None
) -> TimelineEvent:
    event = TimelineEvent(
        issue_id=issue_id,
        actor_id=actor_id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        title=title,
        details=details,
        metadata_json=json.dumps(metadata_dict) if metadata_dict else None
    )
    db.add(event)
    return event

def create_issue_and_route_report(
    db: Session,
    reporter: User,
    issue_type_id: int,
    location_id: int,
    description: str,
    specific_asset: Optional[str] = None,
    photo_url: Optional[str] = None
) -> tuple[Issue, Report]:
    """
    Submits a new report, deterministically routes it to a handler, and creates an underlying Issue.
    """
    issue_type = db.query(IssueType).filter(IssueType.id == issue_type_id, IssueType.is_active.is_(True)).first()
    if not issue_type:
        raise HTTPException(status_code=404, detail="Selected IssueType not found or inactive")

    location = db.query(Location).filter(Location.id == location_id, Location.is_active.is_(True)).first()
    if not location:
        raise HTTPException(status_code=404, detail="Selected Location not found or inactive")

    # 1. Deterministic routing lookup
    assigned_handler = resolve_handler_deterministically(db, issue_type_id, location_id)
    
    # 2. Build Title
    asset_str = f" ({specific_asset})" if specific_asset else ""
    title = f"{issue_type.category} - {issue_type.sub_type}{asset_str} at {location.name}"

    # 3. Create Issue
    issue = Issue(
        issue_type_id=issue_type_id,
        location_id=location_id,
        specific_asset=specific_asset,
        title=title,
        description=description,
        status=IssueStatus.OPEN,
        current_handler_id=assigned_handler.id if assigned_handler else None,
        requires_verification=issue_type.requires_verification
    )
    db.add(issue)
    db.flush() # populate issue.id

    # 4. Create Report
    report = Report(
        issue_id=issue.id,
        reporter_id=reporter.id,
        issue_type_id=issue_type_id,
        location_id=location_id,
        specific_asset=specific_asset,
        description=description,
        photo_url=photo_url,
        status=ReportStatus.LINKED_TO_ISSUE
    )
    db.add(report)
    db.flush()

    # 5. Timeline Events
    create_timeline_event(
        db=db,
        issue_id=issue.id,
        actor_id=reporter.id,
        event_type=TimelineEventType.REPORT_SUBMITTED,
        from_status=None,
        to_status=IssueStatus.OPEN,
        title=f"Initial report submitted by {reporter.full_name}",
        details=description,
        metadata_dict={"report_id": report.id, "reporter_email": reporter.email}
    )

    handler_name = assigned_handler.full_name if assigned_handler else "Unassigned (Pending)"
    create_timeline_event(
        db=db,
        issue_id=issue.id,
        actor_id=None,
        event_type=TimelineEventType.ROUTED,
        from_status=None,
        to_status=IssueStatus.OPEN,
        title=f"Deterministically routed to {handler_name}",
        details=f"Assigned based on routing rules for {issue_type.category} / {issue_type.sub_type} at {location.name}."
    )

    # 6. Notifications
    if assigned_handler:
        notify_user(
            db=db,
            user_id=assigned_handler.id,
            title="New Issue Assigned",
            message=f"New issue '{title}' has been routed to you.",
            issue_id=issue.id
        )

    db.commit()
    db.refresh(issue)
    db.refresh(report)
    return issue, report

def link_report_to_existing_issue(
    db: Session,
    reporter: User,
    existing_issue_id: int,
    issue_type_id: int,
    location_id: int,
    description: str,
    specific_asset: Optional[str] = None,
    photo_url: Optional[str] = None
) -> tuple[Issue, Report]:
    """
    Links a new student submission to an already active existing issue (after deterministic duplicate prompt).
    """
    issue = db.query(Issue).filter(Issue.id == existing_issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Target issue not found")

    report = Report(
        issue_id=issue.id,
        reporter_id=reporter.id,
        issue_type_id=issue_type_id,
        location_id=location_id,
        specific_asset=specific_asset,
        description=description,
        photo_url=photo_url,
        status=ReportStatus.LINKED_TO_ISSUE
    )
    db.add(report)
    db.flush()

    # Timeline event
    create_timeline_event(
        db=db,
        issue_id=issue.id,
        actor_id=reporter.id,
        event_type=TimelineEventType.REPORT_LINKED,
        title=f"Additional report linked by {reporter.full_name}",
        details=description,
        metadata_dict={"report_id": report.id, "reporter_email": reporter.email}
    )

    # Notify handler of increased report count
    if issue.current_handler_id:
        notify_user(
            db=db,
            user_id=issue.current_handler_id,
            title="Additional Student Report Linked",
            message=f"{reporter.full_name} reported the same issue '{issue.title}'.",
            issue_id=issue.id
        )

    db.commit()
    db.refresh(issue)
    db.refresh(report)
    return issue, report

def start_issue_progress(
    db: Session,
    issue_id: int,
    current_user: User
) -> Issue:
    """
    Handler starts working on the assigned issue.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if current_user.role not in [UserRole.ADMIN, UserRole.HIGHER_AUTHORITY] and issue.current_handler_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the assigned handler or admin can update this issue")

    if issue.status not in [IssueStatus.OPEN, IssueStatus.REOPENED]:
        raise HTTPException(status_code=400, detail=f"Cannot start progress on issue with status '{issue.status.value}'")

    prev_status = issue.status
    issue.status = IssueStatus.IN_PROGRESS
    
    create_timeline_event(
        db=db,
        issue_id=issue.id,
        actor_id=current_user.id,
        event_type=TimelineEventType.STARTED_PROGRESS,
        from_status=prev_status,
        to_status=IssueStatus.IN_PROGRESS,
        title=f"Work started by {current_user.full_name}",
        details="Handler acknowledged the issue and commenced resolution."
    )

    notify_affected_students(
        db=db,
        issue_id=issue.id,
        title="Issue In Progress",
        message=f"Handler {current_user.full_name} has started working on '{issue.title}'."
    )

    db.commit()
    db.refresh(issue)
    return issue

def escalate_issue(
    db: Session,
    issue_id: int,
    escalating_user: User,
    reason: str,
    escalated_to_id: Optional[int] = None
) -> Escalation:
    """
    Handler escalates the issue to a higher authority with a mandatory reason.
    Preserves full snapshot history.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if escalating_user.role not in [UserRole.ADMIN] and issue.current_handler_id != escalating_user.id:
        raise HTTPException(status_code=403, detail="Only the assigned handler can escalate this issue")

    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="Escalation reason is required")

    # Find target authority if not specified
    if not escalated_to_id:
        authority = (
            db.query(User)
            .filter(User.role == UserRole.HIGHER_AUTHORITY, User.is_active.is_(True))
            .first()
        )
        if not authority:
            authority = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active.is_(True)).first()
        target_authority_id = authority.id if authority else None
    else:
        target_authority_id = escalated_to_id

    # Build snapshot of history
    reports_snapshot = [
        {"id": r.id, "reporter": r.reporter.full_name, "description": r.description, "created_at": str(r.created_at)}
        for r in issue.reports
    ]
    timeline_snapshot = [
        {"type": t.event_type.value, "title": t.title, "actor": t.actor.full_name if t.actor else "System", "time": str(t.created_at)}
        for t in issue.timeline_events
    ]
    snapshot_data = {
        "issue_id": issue.id,
        "title": issue.title,
        "location": issue.location.name if issue.location else "",
        "category": issue.issue_type.category if issue.issue_type else "",
        "reports": reports_snapshot,
        "timeline": timeline_snapshot
    }

    prev_status = issue.status
    issue.status = IssueStatus.ESCALATED

    escalation = Escalation(
        issue_id=issue.id,
        escalated_by_id=escalating_user.id,
        escalated_to_id=target_authority_id,
        reason=reason,
        previous_status=prev_status.value,
        history_snapshot=json.dumps(snapshot_data)
    )
    db.add(escalation)
    db.flush()

    create_timeline_event(
        db=db,
        issue_id=issue.id,
        actor_id=escalating_user.id,
        event_type=TimelineEventType.ESCALATED,
        from_status=prev_status,
        to_status=IssueStatus.ESCALATED,
        title=f"Escalated by {escalating_user.full_name}",
        details=f"Reason: {reason}",
        metadata_dict={"escalation_id": escalation.id, "escalated_to_id": target_authority_id}
    )

    if target_authority_id:
        notify_user(
            db=db,
            user_id=target_authority_id,
            title="Issue Escalated for Review",
            message=f"Issue '{issue.title}' was escalated by {escalating_user.full_name}: {reason}",
            issue_id=issue.id
        )

    notify_affected_students(
        db=db,
        issue_id=issue.id,
        title="Issue Escalated",
        message=f"Your reported issue '{issue.title}' has been escalated to campus higher authority for resolution."
    )

    db.commit()
    db.refresh(escalation)
    db.refresh(issue)
    return escalation

def resolve_issue_with_evidence(
    db: Session,
    issue_id: int,
    resolving_user: User,
    evidence_type: EvidenceType,
    notes: str,
    attachment_url: Optional[str] = None
) -> ResolutionEvidence:
    """
    Handler or authority marks issue resolved and attaches required evidence.
    If issue_type.requires_verification is True, status becomes RESOLVED_PENDING_VERIFICATION.
    Otherwise becomes VERIFIED_CLOSED.
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    is_handler = issue.current_handler_id == resolving_user.id
    is_privileged = resolving_user.role in [UserRole.ADMIN, UserRole.HIGHER_AUTHORITY]
    if not (is_handler or is_privileged):
        raise HTTPException(status_code=403, detail="Only assigned handler, higher authority, or admin can resolve this issue")

    if not notes or not notes.strip():
        raise HTTPException(status_code=400, detail="Resolution notes/action description is mandatory")

    prev_status = issue.status
    next_status = (
        IssueStatus.RESOLVED_PENDING_VERIFICATION
        if issue.requires_verification
        else IssueStatus.VERIFIED_CLOSED
    )
    issue.status = next_status

    evidence = ResolutionEvidence(
        issue_id=issue.id,
        submitted_by_id=resolving_user.id,
        evidence_type=evidence_type,
        notes=notes,
        attachment_url=attachment_url
    )
    db.add(evidence)
    db.flush()

    status_str = "resolved (pending student verification)" if issue.requires_verification else "resolved and closed"
    create_timeline_event(
        db=db,
        issue_id=issue.id,
        actor_id=resolving_user.id,
        event_type=TimelineEventType.RESOLVED,
        from_status=prev_status,
        to_status=next_status,
        title=f"Marked {status_str} by {resolving_user.full_name}",
        details=f"Evidence ({evidence_type.value}): {notes}",
        metadata_dict={"evidence_id": evidence.id, "attachment_url": attachment_url}
    )

    # Notify affected students
    if issue.requires_verification:
        notif_msg = f"Handler {resolving_user.full_name} has resolved '{issue.title}'. Please verify if the issue is fixed."
    else:
        notif_msg = f"Issue '{issue.title}' has been successfully resolved and closed."

    notify_affected_students(
        db=db,
        issue_id=issue.id,
        title="Issue Resolution Update",
        message=notif_msg
    )

    db.commit()
    db.refresh(evidence)
    db.refresh(issue)
    return evidence

def verify_issue_resolution(
    db: Session,
    issue_id: int,
    verifying_user: User,
    status: VerificationStatus,
    comment: Optional[str] = None
) -> Verification:
    """
    Affected student confirms or disputes the resolution.
    If confirmed -> VERIFIED_CLOSED
    If disputed -> REOPENED
    """
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    if issue.status != IssueStatus.RESOLVED_PENDING_VERIFICATION:
        raise HTTPException(
            status_code=400,
            detail=f"Issue is not pending verification (current status: {issue.status.value})"
        )

    # Verify that the user is an affected student (or admin)
    is_reporter = any(r.reporter_id == verifying_user.id for r in issue.reports)
    if not is_reporter and verifying_user.role not in [UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Only affected students who reported this issue can verify its resolution")

    verification = Verification(
        issue_id=issue.id,
        verified_by_id=verifying_user.id,
        status=status,
        comment=comment
    )
    db.add(verification)
    db.flush()

    prev_status = issue.status
    if status == VerificationStatus.CONFIRMED:
        issue.status = IssueStatus.VERIFIED_CLOSED
        create_timeline_event(
            db=db,
            issue_id=issue.id,
            actor_id=verifying_user.id,
            event_type=TimelineEventType.VERIFIED,
            from_status=prev_status,
            to_status=IssueStatus.VERIFIED_CLOSED,
            title=f"Resolution confirmed by {verifying_user.full_name}",
            details=comment or "Student confirmed that the problem has been satisfactorily fixed."
        )
        if issue.current_handler_id:
            notify_user(
                db=db,
                user_id=issue.current_handler_id,
                title="Resolution Verified & Closed",
                message=f"Student {verifying_user.full_name} confirmed the resolution for '{issue.title}'.",
                issue_id=issue.id
            )
    else: # DISPUTED
        issue.status = IssueStatus.REOPENED
        create_timeline_event(
            db=db,
            issue_id=issue.id,
            actor_id=verifying_user.id,
            event_type=TimelineEventType.DISPUTED,
            from_status=prev_status,
            to_status=IssueStatus.REOPENED,
            title=f"Resolution disputed / reopened by {verifying_user.full_name}",
            details=comment or "Student indicated the problem is still unresolved."
        )
        if issue.current_handler_id:
            notify_user(
                db=db,
                user_id=issue.current_handler_id,
                title="Issue Reopened (Verification Disputed)",
                message=f"Student {verifying_user.full_name} reported that '{issue.title}' is still broken: {comment or 'No comment'}",
                issue_id=issue.id
            )

    db.commit()
    db.refresh(verification)
    db.refresh(issue)
    return verification

def reassign_issue_handler(
    db: Session,
    issue_id: int,
    new_handler_id: int,
    reassigned_by: User,
    reason: Optional[str] = None
) -> Issue:
    """
    Higher authority or admin reassigns an issue to a new handler.
    """
    if reassigned_by.role not in [UserRole.ADMIN, UserRole.HIGHER_AUTHORITY]:
        raise HTTPException(status_code=403, detail="Only admin or higher authority can reassign issues")

    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    new_handler = db.query(User).filter(User.id == new_handler_id, User.is_active.is_(True)).first()
    if not new_handler:
        raise HTTPException(status_code=404, detail="Target handler not found")

    old_handler_name = issue.current_handler.full_name if issue.current_handler else "None"
    issue.current_handler_id = new_handler.id
    
    # If issue was escalated, reassigning resets it to IN_PROGRESS or OPEN
    if issue.status == IssueStatus.ESCALATED:
        issue.status = IssueStatus.IN_PROGRESS

    create_timeline_event(
        db=db,
        issue_id=issue.id,
        actor_id=reassigned_by.id,
        event_type=TimelineEventType.REASSIGNED,
        title=f"Reassigned to {new_handler.full_name} by {reassigned_by.full_name}",
        details=f"Transferred from {old_handler_name}. Reason: {reason or 'Administrative reassignment'}"
    )

    notify_user(
        db=db,
        user_id=new_handler.id,
        title="Issue Reassigned to You",
        message=f"Issue '{issue.title}' has been assigned to you by {reassigned_by.full_name}.",
        issue_id=issue.id
    )

    db.commit()
    db.refresh(issue)
    return issue

