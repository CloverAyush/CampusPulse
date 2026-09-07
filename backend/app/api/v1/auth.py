from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserCreate, UserLogin, UserOut, Token, DemoLoginRequest
from app.services.auth import verify_password, get_password_hash, create_access_token
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=user_in.role,
        department=user_in.department,
        phone=user_in.phone,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role.value)
    return Token(access_token=token, token_type="bearer", user=user)

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is deactivated."
        )

    token = create_access_token(subject=user.id, role=user.role.value)
    return Token(access_token=token, token_type="bearer", user=user)

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/demo-login", response_model=Token)
def demo_login(req: DemoLoginRequest, db: Session = Depends(get_db)):
    """
    Convenience endpoint for switching between personas during evaluation/testing.
    """
    user = db.query(User).filter(User.role == req.role, User.is_active.is_(True)).first()
    if not user:
        # Fallback or create default demo user for this role if none exists
        default_emails = {
            UserRole.STUDENT: "student.aarav@campus.edu",
            UserRole.HANDLER: "facilities.sharma@campus.edu",
            UserRole.HIGHER_AUTHORITY: "dean.verma@campus.edu",
            UserRole.ADMIN: "admin@campus.edu"
        }
        default_names = {
            UserRole.STUDENT: "Aarav Sharma (Student)",
            UserRole.HANDLER: "Rajesh Sharma (Facilities Handler)",
            UserRole.HIGHER_AUTHORITY: "Dr. K. Verma (Dean of Campus Infrastructure)",
            UserRole.ADMIN: "CampusPulse Administrator"
        }
        user = User(
            email=default_emails.get(req.role, f"{req.role.value}@campus.edu"),
            hashed_password=get_password_hash("demo12345"),
            full_name=default_names.get(req.role, f"Demo {req.role.value}"),
            role=req.role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(subject=user.id, role=user.role.value)
    return Token(access_token=token, token_type="bearer", user=user)

