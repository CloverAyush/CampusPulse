from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, parse_pagination
from app.database import get_db
from app.errors import NotFoundError
from app.models.notification import Notification
from app.models.user import User
from app.schemas.issue import Page
from app.schemas.notification import NotificationOut

router = APIRouter()


@router.get("", response_model=Page[NotificationOut])
def get_my_notifications(
    unread_only: bool = Query(default=False),
    limit: Optional[int] = Query(default=None),
    offset: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    resolved_limit, resolved_offset = parse_pagination(limit, offset)

    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))

    total = query.count()
    notifications = (
        query.order_by(desc(Notification.created_at), desc(Notification.id))
        .limit(resolved_limit)
        .offset(resolved_offset)
        .all()
    )

    return Page[NotificationOut](
        items=[NotificationOut.model_validate(item) for item in notifications],
        total=total,
        limit=resolved_limit,
        offset=resolved_offset,
    )


@router.get("/unread-count")
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .count()
    )
    return {"unread_count": count}


@router.post("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if not notification:
        raise NotFoundError("Notification not found")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/read-all")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    updated = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .update({"is_read": True}, synchronize_session=False)
    )
    db.commit()
    return {"marked_read": updated}
