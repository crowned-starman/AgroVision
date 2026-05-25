from sqlalchemy import Column, String, Float, DateTime, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from database import Base


class TerrainAnalysis(Base):
    __tablename__ = "terrain_analyses"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    terrain_id      = Column(UUID(as_uuid=True), ForeignKey("terrains.id"), nullable=False)

    # NDVI
    ndvi_mean       = Column(Float)
    ndvi_std        = Column(Float)
    ndvi_min        = Column(Float)
    ndvi_max        = Column(Float)
    ndvi_monthly    = Column(JSON)   # lista de 12 valores

    # Topografía
    elevation_mean  = Column(Float)
    slope_mean      = Column(Float)
    aspect_mean     = Column(Float)

    # Suelo
    ph_mean         = Column(Float)
    clay_pct        = Column(Float)
    sand_pct        = Column(Float)
    silt_pct        = Column(Float)
    organic_carbon  = Column(Float)

    # Clima
    annual_precip_mm    = Column(Float)
    temp_mean_c         = Column(Float)
    temp_min_c          = Column(Float)
    temp_max_c          = Column(Float)
    precip_seasonality  = Column(Float)

    data_source     = Column(String(50), default="mock")
    computed_at     = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    crop_scores     = relationship("CropScore", back_populates="analysis", cascade="all, delete-orphan")


class CropScore(Base):
    __tablename__ = "crop_scores"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id          = Column(UUID(as_uuid=True), ForeignKey("terrain_analyses.id"), nullable=False)
    crop_id              = Column(String(100), nullable=False)
    crop_name            = Column(String(200), nullable=False)

    score_total          = Column(Float, nullable=False)
    score_breakdown      = Column(JSON)     # {temperatura: 0.9, agua: 0.7, ...}
    limiting_factors     = Column(JSON)     # [{name, severity, message}]
    recommendation_level = Column(String(20))  # alto/medio/bajo/incompatible
    explanation          = Column(String(1000))

    analysis             = relationship("TerrainAnalysis", back_populates="crop_scores")
