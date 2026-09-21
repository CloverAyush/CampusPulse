from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampColumn, utcnow
from app.models.enums import ReportStatus


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    issue_type_id = Column(Integer, ForeignKey("issue_types.id"), nullable=False, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False, index=True)
    specific_asset = Column(String(150), nullable=True)
    description = Column(Text, nullable=False)
    photo_url = Column(String(500), nullable=True)
    status = Column(Enum(ReportStatus, native_enum=False, length=40), default=ReportStatus.SUBMITTED, nullable=False)
    created_at = Column(TimestampColumn, default=utcnow, nullable=False)

    issue = relationship("Issue", back_populates="reports")
    reporter = relationship("User", back_populates="reports", foreign_keys=[reporter_id])
    issue_type = relationship("IssueType", back_populates="reports")
    location = relationship("Location", back_populates="reports")
