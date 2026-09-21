import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.errors import ConflictError, ValidationError
from app.models.enums import UserRole
from app.models.user import User
from app.rate_limit import rate_limit
from app.schemas.user import PasswordChange, Token, UserLogin, UserOut, UserRegister
from app.services.auth import create_access_token, get_password_hash, verify_password
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

login_rate_limit = rate_limit("login", settings.LOGIN_RATE_LIMIT_PER_MINUTE, 60)
register_rate_limit = rate_limit("register", settings.REGISTER_RATE_LIMIT_PER_HOUR, 3600)


def _issue_token(user: User) -> Token:
    token, expires_in = create_access_token(subject=user.id, role=user.role.value)
    return Token(access_token=token, token_type="bearer", expires_in=expires_in, user=UserOut.model_validate(user))


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(register_rate_limit)],
)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """Self-registration always creates a student. Handler, higher-authority and
    admin accounts exist only when an administrator creates them."""
    email = user_in.email.lower()

    user = User(
        email=email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name.strip(),
        role=UserRole.STUDENT,
        department=user_in.department,
        phone=user_in.phone,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ConflictError("An account with this email already exists")

    db.refresh(user)
    logger.info("Student account registered", extra={"new_user_id": user.id})
    return _issue_token(user)


@router.post("/login", response_model=Token, dependencies=[Depends(login_rate_limit)])
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email.lower()).first()

    # Same message and same work for a missing account and a wrong password, so the
    # response cannot be used to discover which emails are registered.
    if not user or not verify_password(login_data.password, user.hashed_password) or not user.is_active:
        logger.info("Failed sign-in attempt")
        raise ValidationError("Incorrect email or password", error_code="invalid_credentials")

    logger.info("Sign-in succeeded", extra={"authenticated_user_id": user.id})
    return _issue_token(user)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password", response_model=UserOut)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise ValidationError("Your current password is incorrect")
    if payload.new_password == payload.current_password:
        raise ValidationError("Choose a password different from your current one")

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    db.refresh(current_user)
    logger.info("Password changed", extra={"changed_user_id": current_user.id})
    return current_user
