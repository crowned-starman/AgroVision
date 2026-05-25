from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.orm.terrain import Terrain
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", summary="Listar terrenos guardados")
def list_terrains(db: Session = Depends(get_db)):
    terrains = db.query(Terrain).order_by(Terrain.created_at.desc()).limit(50).all()
    return [
        {
            "id":         str(t.id),
            "name":       t.name,
            "area_ha":    t.area_ha,
            "geojson":    t.geojson,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in terrains
    ]
