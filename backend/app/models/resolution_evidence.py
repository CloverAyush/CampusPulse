from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.models.enums import EvidenceType

class ResolutionEvidence(Base):
    __tablename__ = "resolution_evidences"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    evidence_type = Column(Enum(EvidenceType), default=EvidenceType.DESCRIPTION, nullable=False)
    notes = Column(Text, nullable=False)
    attachment_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    issue = relationship("Issue", back_populates="evidences")
    submitted_by = relationship("User", back_populates="submitted_evidences", foreign_keys=[submitted_by_id])

