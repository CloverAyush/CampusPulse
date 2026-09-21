from sqlalchemy import Boolean, Column, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampColumn, utcnow


class IssueType(Base):
    __tablename__ = "issue_types"
    __table_args__ = (UniqueConstraint("category", "sub_type", name="uq_issue_type_category_subtype"),)

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    sub_type = Column(String(100), nullable=False, index=True)
    description = Column(String(255), nullable=True)
    requires_verification = Column(Boolean, default=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TimestampColumn, default=utcnow, nullable=False)

    issues = relationship("Issue", back_populates="issue_type")
    reports = relationship("Report", back_populates="issue_type")
    routing_rules = relationship("RoutingRule", back_populates="issue_type")
