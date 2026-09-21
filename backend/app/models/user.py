from sqlalchemy import Boolean, Column, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampColumn, utcnow
from app.models.enums import UserRole


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, native_enum=False, length=32), default=UserRole.STUDENT, nullable=False, index=True)
    department = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TimestampColumn, default=utcnow, nullable=False)

    reports = relationship("Report", back_populates="reporter", foreign_keys="Report.reporter_id")
    assigned_issues = relationship("Issue", back_populates="current_handler", foreign_keys="Issue.current_handler_id")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    verifications = relationship("Verification", back_populates="verified_by")
    submitted_evidences = relationship("ResolutionEvidence", back_populates="submitted_by")
