from sqlalchemy import Boolean, Column, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampColumn, utcnow
from app.models.enums import IssueStatus


class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        Index("ix_issues_type_location_status", "issue_type_id", "location_id", "status"),
    )

    id = Column(Integer, primary_key=True, index=True)
    issue_type_id = Column(Integer, ForeignKey("issue_types.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    specific_asset = Column(String(150), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(Enum(IssueStatus, native_enum=False, length=40), default=IssueStatus.OPEN, nullable=False, index=True)
    current_handler_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    requires_verification = Column(Boolean, default=True, nullable=False)
    needs_triage = Column(Boolean, default=False, nullable=False, index=True)
    affected_student_count = Column(Integer, default=1, nullable=False)
    created_at = Column(TimestampColumn, default=utcnow, nullable=False)
    updated_at = Column(TimestampColumn, default=utcnow, onupdate=utcnow, nullable=False)

    issue_type = relationship("IssueType", back_populates="issues")
    location = relationship("Location", back_populates="issues")
    current_handler = relationship("User", back_populates="assigned_issues", foreign_keys=[current_handler_id])
    reports = relationship("Report", back_populates="issue", order_by="Report.created_at.asc()")
    escalations = relationship("Escalation", back_populates="issue", order_by="Escalation.created_at.desc()")
    evidences = relationship("ResolutionEvidence", back_populates="issue", order_by="ResolutionEvidence.created_at.desc()")
    verifications = relationship("Verification", back_populates="issue", order_by="Verification.created_at.desc()")
    timeline_events = relationship("TimelineEvent", back_populates="issue", order_by="TimelineEvent.created_at.asc()")
    notifications = relationship("Notification", back_populates="issue")
