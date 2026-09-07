from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    escalated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    escalated_to_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # Authority
    reason = Column(Text, nullable=False)
    previous_status = Column(String(50), nullable=False)
    history_snapshot = Column(Text, nullable=True) # JSON snapshot of timeline/reports at escalation time
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    issue = relationship("Issue", back_populates="escalations")
    escalated_by = relationship("User", foreign_keys=[escalated_by_id])
    escalated_to = relationship("User", foreign_keys=[escalated_to_id])

