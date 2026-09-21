from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampColumn, utcnow
from app.models.enums import IssueStatus, TimelineEventType


class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(Enum(TimelineEventType, native_enum=False, length=40), nullable=False)
    from_status = Column(Enum(IssueStatus, native_enum=False, length=40), nullable=True)
    to_status = Column(Enum(IssueStatus, native_enum=False, length=40), nullable=True)
    title = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(TimestampColumn, default=utcnow, nullable=False)

    issue = relationship("Issue", back_populates="timeline_events")
    actor = relationship("User", foreign_keys=[actor_id])
