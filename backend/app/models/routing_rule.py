from sqlalchemy import Column, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(Integer, primary_key=True, index=True)
    issue_type_id = Column(Integer, ForeignKey("issue_types.id"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)
    handler_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    priority = Column(Integer, default=10, nullable=False) # higher number = higher priority
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    issue_type = relationship("IssueType", back_populates="routing_rules")
    location = relationship("Location", back_populates="routing_rules")
    handler = relationship("User", foreign_keys=[handler_id])

