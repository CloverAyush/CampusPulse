from sqlalchemy import Column, Enum, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base import TimestampColumn, utcnow
from app.models.enums import VerificationStatus


class Verification(Base):
    __tablename__ = "verifications"
    __table_args__ = (
        UniqueConstraint("issue_id", "verified_by_id", "resolution_round", name="uq_verification_per_round"),
    )

    id = Column(Integer, primary_key=True, index=True)
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    verified_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    resolution_round = Column(Integer, default=1, nullable=False)
    status = Column(Enum(VerificationStatus, native_enum=False, length=32), nullable=False)
    comment = Column(Text, nullable=True)
    created_at = Column(TimestampColumn, default=utcnow, nullable=False)

    issue = relationship("Issue", back_populates="verifications")
    verified_by = relationship("User", back_populates="verifications", foreign_keys=[verified_by_id])
