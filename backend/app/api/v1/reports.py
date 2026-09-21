import logging

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, parse_pagination
from app.config import settings
from app.database import get_db
from app.models.report import Report
from app.models.user import User
from app.rate_limit import rate_limit
from app.schemas.issue import Page
from app.schemas.report import (
    DuplicateCheckRequest,
    DuplicateCheckResponse,
    ReportCreate,
    ReportOut,
)
from app.services.duplicate_check import check_duplicate_issues
from app.services.issue_state_machine import (
    create_issue_and_route_report,
    link_report_to_existing_issue,
)

logger = logging.getLogger(__name__)
router = APIRouter()

submit_rate_limit = rate_limit("submit_report", settings.WRITE_RATE_LIMIT_PER_MINUTE, 60)


@router.post("/check-duplicate", response_model=DuplicateCheckResponse)
def check_duplicate(
    payload: DuplicateCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Structured lookup on (issue type, location, asset). Returns suggestions only:
    the student chooses whether their report joins an existing issue."""
    return check_duplicate_issues(
        db=db,
        issue_type_id=payload.issue_type_id,
        location_id=payload.location_id,
        specific_asset=payload.specific_asset,
        viewer_id=current_user.id,
    )


@router.post(
    "",
    response_model=ReportOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(submit_rate_limit)],
)
def submit_report(
    report_in: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if report_in.existing_issue_id is not None:
        _, report = link_report_to_existing_issue(
            db=db,
            reporter=current_user,
            existing_issue_id=report_in.existing_issue_id,
            issue_type_id=report_in.issue_type_id,
            location_id=report_in.location_id,
            description=report_in.description,
            specific_asset=report_in.specific_asset,
            photo_url=report_in.photo_url,
        )
    else:
        _, report = create_issue_and_route_report(
            db=db,
            reporter=current_user,
            issue_type_id=report_in.issue_type_id,
            location_id=report_in.location_id,
            description=report_in.description,
            specific_asset=report_in.specific_asset,
            photo_url=report_in.photo_url,
        )
    return report


@router.get("/my", response_model=Page[ReportOut])
def get_my_reports(
    limit: int = Query(default=None),
    offset: int = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resolved_limit, resolved_offset = parse_pagination(limit, offset)

    base = db.query(Report).filter(Report.reporter_id == current_user.id)
    total = base.count()
    reports = (
        base.options(
            joinedload(Report.issue_type),
            joinedload(Report.location),
        )
        .order_by(Report.created_at.desc(), Report.id.desc())
        .limit(resolved_limit)
        .offset(resolved_offset)
        .all()
    )

    return Page[ReportOut](
        items=[ReportOut.model_validate(report) for report in reports],
        total=total,
        limit=resolved_limit,
        offset=resolved_offset,
    )
