from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models.user import User
from app.models.issue import Issue
from app.models.report import Report
from app.models.enums import UserRole, IssueStatus
from app.schemas.issue import IssueOut, IssueDetailOut, IssueReassignRequest
from app.schemas.resolution_evidence import ResolutionEvidenceCreate, ResolutionEvidenceOut
from app.schemas.verification import VerificationCreate, VerificationOut
from app.schemas.escalation import EscalationCreate, EscalationOut
from app.schemas.timeline import TimelineEventOut
from app.services.issue_state_machine import (
    start_issue_progress,
    escalate_issue,
    resolve_issue_with_evidence,
    verify_issue_resolution,
    reassign_issue_handler
)
from app.api.deps import get_current_user

router = APIRouter()

@router.get("", response_model=List[IssueOut])
def list_issues(
    status_filter: Optional[IssueStatus] = Query(None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List issues relevant to the current user's role:
    - Student: Issues that have reports submitted by this student.
    - Handler: Issues assigned to this handler.
    - Higher Authority: Escalated issues (or all campus issues if no filter).
    - Admin: All issues.
    """
    query = db.query(Issue)

    if current_user.role == UserRole.STUDENT:
        # Issues where this student is one of the reporters
        subquery = db.query(Report.issue_id).filter(Report.reporter_id == current_user.id).subquery()
        query = query.filter(Issue.id.in_(subquery))
    elif current_user.role == UserRole.HANDLER:
        # Assigned to this handler
        query = query.filter(Issue.current_handler_id == current_user.id)
    elif current_user.role == UserRole.HIGHER_AUTHORITY:
        # If no explicit filter passed, show ESCALATED issues by default or all
        if not status_filter:
            # Show escalated first or all
            pass
    elif current_user.role == UserRole.ADMIN:
        pass

    if status_filter:
        query = query.filter(Issue.status == status_filter)

    issues = query.order_by(desc(Issue.updated_at)).all()

    # Populate report_count for response
    results = []
    for issue in issues:
        count = db.query(func.count(Report.id)).filter(Report.issue_id == issue.id).scalar() or 0
        issue_out = IssueOut.model_validate(issue)
        issue_out.report_count = count
        results.append(issue_out)

    return results

@router.get("/{id}", response_model=IssueDetailOut)
def get_issue(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full issue details with all linked reports, evidences, verifications, and history.
    """
    issue = db.query(Issue).filter(Issue.id == id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    count = db.query(func.count(Report.id)).filter(Report.issue_id == issue.id).scalar() or 0
    detail = IssueDetailOut.model_validate(issue)
    detail.report_count = count
    return detail

@router.get("/{id}/history", response_model=List[TimelineEventOut])
def get_issue_history(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the complete chronological audit timeline for an issue.
    """
    issue = db.query(Issue).filter(Issue.id == id).first()
    if not issue:
        raise HTTPException(status_code=404, detail="Issue not found")

    return issue.timeline_events

@router.post("/{id}/progress", response_model=IssueDetailOut)
def mark_in_progress(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Handler marks an issue as IN_PROGRESS.
    """
    issue = start_issue_progress(db=db, issue_id=id, current_user=current_user)
    count = db.query(func.count(Report.id)).filter(Report.issue_id == issue.id).scalar() or 0
    detail = IssueDetailOut.model_validate(issue)
    detail.report_count = count
    return detail

@router.post("/{id}/resolve", response_model=ResolutionEvidenceOut)
def resolve_issue(
    id: int,
    evidence_in: ResolutionEvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Handler or Authority marks the issue resolved and attaches evidence.
    """
    evidence = resolve_issue_with_evidence(
        db=db,
        issue_id=id,
        resolving_user=current_user,
        evidence_type=evidence_in.evidence_type,
        notes=evidence_in.notes,
        attachment_url=evidence_in.attachment_url
    )
    return evidence

@router.post("/{id}/escalate", response_model=EscalationOut)
def escalate_issue_endpoint(
    id: int,
    escalation_in: EscalationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Handler escalates the issue with a mandatory reason. Full history snapshot is saved.
    """
    escalation = escalate_issue(
        db=db,
        issue_id=id,
        escalating_user=current_user,
        reason=escalation_in.reason,
        escalated_to_id=escalation_in.escalated_to_id
    )
    return escalation

@router.post("/{id}/verify", response_model=VerificationOut)
def verify_issue(
    id: int,
    verification_in: VerificationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Affected student confirms or disputes the resolution.
    """
    verification = verify_issue_resolution(
        db=db,
        issue_id=id,
        verifying_user=current_user,
        status=verification_in.status,
        comment=verification_in.comment
    )
    return verification

@router.post("/{id}/reassign", response_model=IssueDetailOut)
def reassign_issue(
    id: int,
    req: IssueReassignRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Higher authority or admin reassigns the issue to another handler.
    """
    issue = reassign_issue_handler(
        db=db,
        issue_id=id,
        new_handler_id=req.handler_id,
        reassigned_by=current_user,
        reason=req.reason
    )
    count = db.query(func.count(Report.id)).filter(Report.issue_id == issue.id).scalar() or 0
    detail = IssueDetailOut.model_validate(issue)
    detail.report_count = count
    return detail

