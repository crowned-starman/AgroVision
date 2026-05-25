from pydantic import BaseModel, Field
from typing import Optional, Any
from uuid import UUID
from datetime import datetime


# ── Terrain ──────────────────────────────────────────────
class TerrainCreate(BaseModel):
    name: Optional[str] = None
    geojson: dict = Field(..., description="GeoJSON Polygon del terreno")


class TerrainResponse(BaseModel):
    id: UUID
    name: Optional[str]
    area_ha: Optional[float]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Analysis request ──────────────────────────────────────
class AnalyzeRequest(BaseModel):
    geojson: dict = Field(..., description="GeoJSON Polygon")
    name: Optional[str] = None


# ── Feature set (lo que extraemos del terreno) ───────────
class TerrainFeatures(BaseModel):
    ndvi_mean: float
    ndvi_std: float
    ndvi_min: float
    ndvi_max: float
    ndvi_monthly: list[float]
    elevation_mean: float
    slope_mean: float
    aspect_mean: float
    ph_mean: float
    clay_pct: float
    sand_pct: float
    silt_pct: float
    organic_carbon: float
    annual_precip_mm: float
    temp_mean_c: float
    temp_min_c: float
    temp_max_c: float
    precip_seasonality: float
    data_source: str


# ── Crop score ────────────────────────────────────────────
class CropScoreResponse(BaseModel):
    crop_id: str
    crop_name: str
    score_total: float
    score_breakdown: dict[str, float]
    limiting_factors: list[dict]
    recommendation_level: str
    explanation: str


# ── Full analysis response ────────────────────────────────
class AnalysisResponse(BaseModel):
    analysis_id: UUID
    terrain_id: UUID
    features: TerrainFeatures
    scores: list[CropScoreResponse]
    computed_at: datetime
    data_source: str
