from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampColumn, utcnow


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    escalated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    escalated_to_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    reason = Column(Text, nullable=False)
    previous_status = Column(String(50), nullable=False)
    history_snapshot = Column(Text, nullable=True)
    created_at = Column(TimestampColumn, default=utcnow, nullable=False)

    issue = relationship("Issue", back_populates="escalations")
    escalated_by = relationship("User", foreign_keys=[escalated_by_id])
    escalated_to = relationship("User", foreign_keys=[escalated_to_id])
