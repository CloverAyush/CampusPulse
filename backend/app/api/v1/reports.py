from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.report import Report
from app.schemas.report import (
    ReportCreate,
    ReportOut,
    DuplicateCheckRequest,
    DuplicateCheckResponse
)
from app.schemas.issue import IssueDetailOut
from app.services.duplicate_check import check_duplicate_issues
from app.services.issue_state_machine import (
    create_issue_and_route_report,
    link_report_to_existing_issue
)
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
def check_duplicate(
    req: DuplicateCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deterministically checks if an active issue exists with identical structured parameters
    (issue_type_id + location_id + optional asset), and returns it as a suggestion.
    """
    return check_duplicate_issues(
        db=db,
        issue_type_id=req.issue_type_id,
        location_id=req.location_id,
        specific_asset=req.specific_asset
    )

@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def submit_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submits a report.
    - If existing_issue_id is passed, links the report to the existing issue.
    - Otherwise, deterministically routes to a handler and creates a new issue.
    """
    if report_in.existing_issue_id:
        issue, report = link_report_to_existing_issue(
            db=db,
            reporter=current_user,
            existing_issue_id=report_in.existing_issue_id,
            issue_type_id=report_in.issue_type_id,
            location_id=report_in.location_id,
            description=report_in.description,
            specific_asset=report_in.specific_asset,
            photo_url=report_in.photo_url
        )
    else:
        issue, report = create_issue_and_route_report(
            db=db,
            reporter=current_user,
            issue_type_id=report_in.issue_type_id,
            location_id=report_in.location_id,
            description=report_in.description,
            specific_asset=report_in.specific_asset,
            photo_url=report_in.photo_url
        )
    
    return report

@router.get("/my", response_model=List[ReportOut])
def get_my_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns all reports submitted by the logged-in student.
    """
    reports = (
        db.query(Report)
        .filter(Report.reporter_id == current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return reports

