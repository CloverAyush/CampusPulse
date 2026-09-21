from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampColumn, utcnow


class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    code = Column(String(50), nullable=False, unique=True, index=True)
    building = Column(String(100), nullable=False, index=True)
    floor = Column(String(50), nullable=True)
    room = Column(String(50), nullable=True)
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(TimestampColumn, default=utcnow, nullable=False)

    parent = relationship("Location", remote_side=[id], backref="children")
    issues = relationship("Issue", back_populates="location")
    reports = relationship("Report", back_populates="location")
    routing_rules = relationship("RoutingRule", back_populates="location")
