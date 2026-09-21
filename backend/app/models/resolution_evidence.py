from sqlalchemy import Column, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampColumn, utcnow
from app.models.enums import EvidenceType


class ResolutionEvidence(Base):
    __tablename__ = "resolution_evidences"

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    evidence_type = Column(Enum(EvidenceType, native_enum=False, length=40), default=EvidenceType.DESCRIPTION, nullable=False)
    notes = Column(Text, nullable=False)
    attachment_url = Column(String(500), nullable=True)
    resolution_round = Column(Integer, default=1, nullable=False)
    created_at = Column(TimestampColumn, default=utcnow, nullable=False)

    issue = relationship("Issue", back_populates="evidences")
    submitted_by = relationship("User", back_populates="submitted_evidences", foreign_keys=[submitted_by_id])
