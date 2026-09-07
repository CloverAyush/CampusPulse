from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.issue import Issue
from app.models.report import Report
from app.models.enums import IssueStatus
from app.schemas.report import DuplicateIssueCandidate, DuplicateCheckResponse

ACTIVE_STATUSES = [
    IssueStatus.OPEN,
    IssueStatus.IN_PROGRESS,
    IssueStatus.ESCALATED,
    IssueStatus.REOPENED,
    IssueStatus.RESOLVED_PENDING_VERIFICATION
]

def check_duplicate_issues(
    db: Session,
    issue_type_id: int,
    location_id: int,
    specific_asset: Optional[str] = None
) -> DuplicateCheckResponse:
    """
    Deterministically checks if any active issues match the structured fields:
    (issue_type_id, location_id, and optionally specific_asset).
    
    Returns structured suggestion candidates so the student can decide whether
    their report is the same problem or a distinct one.
    """
    query = (
        db.query(Issue)
        .filter(
            Issue.issue_type_id == issue_type_id,
            Issue.location_id == location_id,
            Issue.status.in_(ACTIVE_STATUSES)
        )
        .order_by(Issue.created_at.desc())
    )

    existing_issues = query.all()

    candidates: List[DuplicateIssueCandidate] = []
    
    # Normalize input asset
    norm_input_asset = specific_asset.strip().lower() if specific_asset else ""

    for issue in existing_issues:
        # Asset matching logic:
        # If neither has specific asset, they match.
        # If both have specific asset, compare normalized strings.
        # If one has specific asset and one doesn't, still suggest because they are in the same room/type.
        is_candidate = True
        norm_issue_asset = issue.specific_asset.strip().lower() if issue.specific_asset else ""

        if norm_input_asset and norm_issue_asset:
            # If both specified different assets (e.g. Fan 1 vs Fan 4), still present with explicit asset label
            pass

        report_count = db.query(func.count(Report.id)).filter(Report.issue_id == issue.id).scalar() or 0

        candidates.append(
            DuplicateIssueCandidate(
                issue_id=issue.id,
                title=issue.title,
                description=issue.description,
                status=issue.status.value,
                created_at=issue.created_at,
                report_count=report_count,
                location_name=issue.location.name if issue.location else "Unknown Location",
                issue_category=issue.issue_type.category if issue.issue_type else "General",
                issue_sub_type=issue.issue_type.sub_type if issue.issue_type else "General",
                specific_asset=issue.specific_asset
            )
        )

    if candidates:
        return DuplicateCheckResponse(
            has_match=True,
            message=f"Found {len(candidates)} existing active issue(s) matching this type and location.",
            candidates=candidates
        )
    else:
        return DuplicateCheckResponse(
            has_match=False,
            message="No matching active issue found.",
            candidates=[]
        )

