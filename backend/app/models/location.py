from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), nullable=False)  # e.g., "Room 204", "Floor 2", "Block A (Main Academic Wing)"
    code = Column(String(50), nullable=False, unique=True, index=True) # e.g., "BLK-A-FL-2-RM-204"
    building = Column(String(100), nullable=False, index=True)  # e.g., "Block A"
    floor = Column(String(50), nullable=True)                  # e.g., "2nd Floor"
    room = Column(String(50), nullable=True)                   # e.g., "Room 204"
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Hierarchical relationship
    parent = relationship("Location", remote_side=[id], backref="children")
    issues = relationship("Issue", back_populates="location")
    reports = relationship("Report", back_populates="location")
    routing_rules = relationship("RoutingRule", back_populates="location")

