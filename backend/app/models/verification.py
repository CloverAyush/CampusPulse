from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.models.enums import VerificationStatus

class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(Enum(VerificationStatus), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    issue = relationship("Issue", back_populates="verifications")
    verified_by = relationship("User", back_populates="verifications", foreign_keys=[verified_by_id])

