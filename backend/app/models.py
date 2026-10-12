from sqlalchemy import Column, String, Numeric, Date, DateTime, Boolean, Integer, Text, ForeignKey, BigInteger
from sqlalchemy.sql import func
from app.database import Base


class LandRecord(Base):
    __tablename__ = "land_records"

    record_id = Column(String(50), primary_key=True, index=True)
    owner_name = Column(String(150), index=True)
    survey_number = Column(String(50), nullable=False, index=True)
    land_area_acres = Column(Numeric(10, 2), nullable=False, default=0.00)
    village = Column(String(100), nullable=False)
    mandal = Column(String(100), nullable=False)
    district = Column(String(100), nullable=False, index=True)
    state = Column(String(100), nullable=False)
    registration_number = Column(String(100))
    registration_date = Column(Date)
    document_type = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class OwnershipHistory(Base):
    __tablename__ = "ownership_history"

    history_id = Column(String(50), primary_key=True, index=True)
    survey_number = Column(String(50), nullable=False, index=True)
    owner_name = Column(String(150), nullable=False)
    transfer_date = Column(Date, index=True)
    transfer_type = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class DocumentRecord(Base):
    __tablename__ = "document_records"

    document_id = Column(String(50), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size_bytes = Column(BigInteger, nullable=False)
    upload_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    ocr_status = Column(String(50), default="PENDING", index=True)
    extracted_text = Column(Text)
    extracted_owner_name = Column(String(150))
    extracted_survey_number = Column(String(50))
    extracted_land_area = Column(Numeric(10, 2))
    extracted_location = Column(String(255))
    ocr_confidence_score = Column(Numeric(5, 2))


class VerificationResult(Base):
    __tablename__ = "verification_results"

    verification_id = Column(String(50), primary_key=True, index=True)
    document_id = Column(String(50), ForeignKey("document_records.document_id", ondelete="CASCADE"), nullable=False, index=True)
    matched_record_id = Column(String(50), ForeignKey("land_records.record_id", ondelete="SET NULL"))
    owner_match = Column(Boolean, default=False)
    survey_number_match = Column(Boolean, default=False)
    land_area_match = Column(Boolean, default=False)
    verification_status = Column(String(50), nullable=False, default="UNVERIFIED", index=True)
    detected_anomalies = Column(Text)
    verification_timestamp = Column(DateTime(timezone=True), server_default=func.now())


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    assessment_id = Column(String(50), primary_key=True, index=True)
    verification_id = Column(String(50), ForeignKey("verification_results.verification_id", ondelete="CASCADE"), nullable=False, index=True)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False, index=True)
    ownership_continuity_score = Column(Integer, default=0)
    area_discrepancy_score = Column(Integer, default=0)
    encumbrance_score = Column(Integer, default=0)
    recommendations = Column(Text)
    assessed_at = Column(DateTime(timezone=True), server_default=func.now())
