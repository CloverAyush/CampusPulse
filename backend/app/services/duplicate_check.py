from typing import Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.enums import IssueStatus
from app.models.issue import Issue
from app.models.report import Report
from app.schemas.report import DuplicateCheckResponse, DuplicateIssueCandidate

ACTIVE_STATUSES = [
    IssueStatus.OPEN,
    IssueStatus.IN_PROGRESS,
    IssueStatus.ESCALATED,
    IssueStatus.REOPENED,
    IssueStatus.RESOLVED_PENDING_VERIFICATION,
]

MAX_CANDIDATES = 10


def normalize_asset(asset: Optional[str]) -> str:
    return asset.strip().casefold() if asset else ""


def check_duplicate_issues(
    db: Session,
    issue_type_id: int,
    location_id: int,
    specific_asset: Optional[str] = None,
    viewer_id: Optional[int] = None,
) -> DuplicateCheckResponse:
    """Structured match on (issue type, location), refined by asset. Nothing here reads
    the description: matching is deterministic and the student always decides."""
    issues = (
        db.query(Issue)
        .options(joinedload(Issue.location), joinedload(Issue.issue_type))
        .filter(
            Issue.issue_type_id == issue_type_id,
            Issue.location_id == location_id,
            Issue.status.in_(ACTIVE_STATUSES),
        )
        .order_by(Issue.created_at.desc())
        .limit(MAX_CANDIDATES)
        .all()
    )

    if not issues:
        return DuplicateCheckResponse(
            has_match=False,
            message="No matching active issue found.",
            candidates=[],
        )

    issue_ids = [issue.id for issue in issues]

    report_totals: Dict[int, int] = dict(
        db.query(Report.issue_id, func.count(Report.id))
        .filter(Report.issue_id.in_(issue_ids))
        .group_by(Report.issue_id)
        .all()
    )
    affected_totals: Dict[int, int] = dict(
        db.query(Report.issue_id, func.count(func.distinct(Report.reporter_id)))
        .filter(Report.issue_id.in_(issue_ids))
        .group_by(Report.issue_id)
        .all()
    )

    already_reported: set[int] = set()
    if viewer_id is not None:
        already_reported = {
            issue_id
            for (issue_id,) in db.query(Report.issue_id)
            .filter(Report.issue_id.in_(issue_ids), Report.reporter_id == viewer_id)
            .distinct()
            .all()
        }

    requested_asset = normalize_asset(specific_asset)

    candidates: List[DuplicateIssueCandidate] = []
    for issue in issues:
        existing_asset = normalize_asset(issue.specific_asset)
        asset_match = (
            not requested_asset or not existing_asset or requested_asset == existing_asset
        )
        candidates.append(
            DuplicateIssueCandidate(
                issue_id=issue.id,
                title=issue.title,
                description=issue.description,
                status=issue.status.value,
                created_at=issue.created_at,
                affected_student_count=affected_totals.get(issue.id, 0),
                report_count=report_totals.get(issue.id, 0),
                location_name=issue.location.name if issue.location else "Unknown location",
                issue_category=issue.issue_type.category if issue.issue_type else "Uncategorised",
                issue_sub_type=issue.issue_type.sub_type if issue.issue_type else "Uncategorised",
                specific_asset=issue.specific_asset,
                asset_match=asset_match,
                already_reported_by_you=issue.id in already_reported,
            )
        )

    # Exact asset matches are the likeliest same-problem candidates, so show them first.
    candidates.sort(key=lambda candidate: (not candidate.asset_match, -candidate.issue_id))

    return DuplicateCheckResponse(
        has_match=True,
        message=(
            f"{len(candidates)} active issue(s) already reported for this type and location. "
            "Pick the one that matches, or submit yours as a separate problem."
        ),
        candidates=candidates,
    )
