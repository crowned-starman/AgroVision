from sqlalchemy import Column, String, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from datetime import datetime, timezone
import uuid
from database import Base


class Terrain(Base):
    __tablename__ = "terrains"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name        = Column(String(200), nullable=True)
    polygon     = Column(Geometry("POLYGON", srid=4326), nullable=False)
    area_ha     = Column(Float, nullable=True)
    geojson     = Column(JSON, nullable=False)   # copia original del frontend
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
