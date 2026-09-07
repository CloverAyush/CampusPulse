from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.notification import Notification
from app.models.report import Report

def notify_user(
    db: Session,
    user_id: int,
    title: str,
    message: str,
    issue_id: Optional[int] = None
) -> Notification:
    notif = Notification(
        user_id=user_id,
        issue_id=issue_id,
        title=title,
        message=message,
        is_read=False
    )
    db.add(notif)
    return notif

def notify_affected_students(
    db: Session,
    issue_id: int,
    title: str,
    message: str,
    exclude_user_id: Optional[int] = None
) -> List[Notification]:
    """
    Sends notifications to all students who submitted linked reports for this issue.
    """
    reporters = (
        db.query(Report.reporter_id)
        .filter(Report.issue_id == issue_id)
        .distinct()
        .all()
    )
    
    notifs = []
    for (reporter_id,) in reporters:
        if exclude_user_id and reporter_id == exclude_user_id:
            continue
        notifs.append(notify_user(db, reporter_id, title, message, issue_id))
    
    return notifs

