from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.models.enums import TimelineEventType, IssueStatus

class TimelineEvent(Base):
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    event_type = Column(Enum(TimelineEventType), nullable=False)
    from_status = Column(Enum(IssueStatus), nullable=True)
    to_status = Column(Enum(IssueStatus), nullable=True)
    title = Column(String(255), nullable=False)
    details = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True) # Optional JSON string for extra structured context
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    issue = relationship("Issue", back_populates="timeline_events")
    actor = relationship("User", foreign_keys=[actor_id])

