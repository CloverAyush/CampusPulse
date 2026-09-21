import logging
from typing import List, Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.errors import DomainError, PermissionDeniedError, ValidationError

from app.logging_config import user_id_var
from app.models.enums import UserRole
from app.models.issue import Issue
from app.models.report import Report
from app.models.user import User
from app.services.auth import decode_access_token

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


class UnauthenticatedError(DomainError):
    status_code = 401
    error_code = "unauthenticated"


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> User:
    if not credentials:
        raise UnauthenticatedError("Sign in to continue")

    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise UnauthenticatedError("Your session has expired. Sign in again.")

    subject = payload.get("sub")
    try:
        user_id = int(subject)
    except (TypeError, ValueError):
        logger.warning("Token subject was not a user id")
        raise UnauthenticatedError("Your session is not valid. Sign in again.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise UnauthenticatedError("This account is no longer active")

    user_id_var.set(str(user.id))
    request.state.user_id = user.id
    return user


def require_roles(allowed_roles: List[UserRole]):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                "Blocked a request from a role without permission",
                extra={"required": [r.value for r in allowed_roles], "actual": current_user.role.value},
            )
            raise PermissionDeniedError("You do not have permission to perform this action")
        return current_user

    return role_checker


require_admin = require_roles([UserRole.ADMIN])
require_staff = require_roles([UserRole.HANDLER, UserRole.HIGHER_AUTHORITY, UserRole.ADMIN])


def is_affected_reporter(db: Session, issue_id: int, user_id: int) -> bool:
    return (
        db.query(Report.id)
        .filter(Report.issue_id == issue_id, Report.reporter_id == user_id)
        .first()
        is not None
    )


def can_see_contact_details(user: User, issue: Issue) -> bool:
    """Staff working an issue need to reach the people who reported it. Other
    students browsing the campus board do not."""
    if user.role in (UserRole.ADMIN, UserRole.HIGHER_AUTHORITY):
        return True
    return user.role == UserRole.HANDLER and issue.current_handler_id == user.id


def parse_pagination(limit: Optional[int], offset: Optional[int]) -> tuple[int, int]:
    resolved_limit = settings.DEFAULT_PAGE_SIZE if limit is None else limit
    resolved_offset = 0 if offset is None else offset

    if resolved_limit < 1 or resolved_limit > settings.MAX_PAGE_SIZE:
        raise ValidationError(f"limit must be between 1 and {settings.MAX_PAGE_SIZE}")
    if resolved_offset < 0:
        raise ValidationError("offset may not be negative")

    return resolved_limit, resolved_offset
