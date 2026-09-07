from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class IssueType(Base):
    __tablename__ = "issue_types"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)  # e.g., "Electrical", "Plumbing", "Wi-Fi", "Cleanliness", "Water Supply", "Library", "Transport"
    sub_type = Column(String(100), nullable=False, index=True)   # e.g., "Ceiling Fan", "Light / Bulb", "Tap Leakage", "Router Offline", "Dustbin Full"
    description = Column(String(255), nullable=True)
    requires_verification = Column(Boolean, default=True, nullable=False)  # Configurable per issue type
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    issues = relationship("Issue", back_populates="issue_type")
    reports = relationship("Report", back_populates="issue_type")
    routing_rules = relationship("RoutingRule", back_populates="issue_type")

