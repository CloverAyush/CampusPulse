import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.models.report import Report

logger = logging.getLogger(__name__)


def notify_user(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    issue_id: Optional[int] = None,
) -> Notification:
    notification = Notification(
        user_id=user_id,
        issue_id=issue_id,
        title=title,
        message=message,
        is_read=False,
    )
    db.add(notification)
    return notification


def affected_reporter_ids(db: Session, issue_id: int) -> List[int]:
    return [
        reporter_id
        for (reporter_id,) in db.query(Report.reporter_id)
        .filter(Report.issue_id == issue_id)
        .distinct()
        .all()
    ]


def notify_affected_students(
    db: Session,
    issue_id: int,
    title: str,
    message: str,
    exclude_user_id: Optional[int] = None,
) -> List[Notification]:
    notifications = []
    for reporter_id in affected_reporter_ids(db, issue_id):
        if exclude_user_id is not None and reporter_id == exclude_user_id:
            continue
        notifications.append(notify_user(db, reporter_id, title, message, issue_id))

    logger.info(
        "Queued notifications for affected students",
        extra={"issue_id": issue_id, "recipient_count": len(notifications)},
    )
    return notifications
