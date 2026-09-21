from sqlalchemy import Boolean, Column, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampColumn, utcnow


class RoutingRule(Base):
    __tablename__ = "routing_rules"

    id = Column(Integer, primary_key=True, index=True)
    issue_type_id = Column(Integer, ForeignKey("issue_types.id"), nullable=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True, index=True)
    handler_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    priority = Column(Integer, default=10, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TimestampColumn, default=utcnow, nullable=False)

    issue_type = relationship("IssueType", back_populates="routing_rules")
    location = relationship("Location", back_populates="routing_rules")
    handler = relationship("User", foreign_keys=[handler_id])
