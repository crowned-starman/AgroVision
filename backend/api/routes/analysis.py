from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from geoalchemy2.functions import ST_GeomFromGeoJSON, ST_Area, ST_Transform
from shapely.geometry import shape, mapping
import json
import logging

from database import get_db
from models.orm.terrain import Terrain
from models.orm.analysis import TerrainAnalysis, CropScore
from models.schemas.analysis import AnalyzeRequest, AnalysisResponse, TerrainFeatures, CropScoreResponse
from modules.geo.feature_extractor import validate_and_fix_polygon, calculate_area_ha, extract_features
from modules.scoring.engine import run_scoring

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/analyze", response_model=AnalysisResponse, summary="Analizar terreno")
def analyze_terrain(request: AnalyzeRequest, db: Session = Depends(get_db)):
    """
    Endpoint principal. Recibe un GeoJSON de polígono, extrae features
    ambientales y calcula scores de compatibilidad para todos los cultivos.
    """
    # 1. Validar polígono
    try:
        clean_geojson = validate_and_fix_polygon(request.geojson)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 2. Calcular área
    area_ha = calculate_area_ha(clean_geojson)
    logger.info(f"Analizando terreno: {area_ha:.2f} ha")

    # 3. Guardar terreno en DB
    geojson_str = json.dumps(clean_geojson)
    terrain = Terrain(
        name    = request.name or f"Terreno {area_ha:.1f} ha",
        polygon = ST_GeomFromGeoJSON(geojson_str),
        area_ha = area_ha,
        geojson = clean_geojson,
    )
    db.add(terrain)
    db.flush()  # obtener terrain.id sin commit

    # 4. Extraer features ambientales (mock o GEE)
    features_dict = extract_features(clean_geojson)

    # 5. Guardar análisis en DB
    analysis = TerrainAnalysis(
        terrain_id         = terrain.id,
        ndvi_mean          = features_dict["ndvi_mean"],
        ndvi_std           = features_dict["ndvi_std"],
        ndvi_min           = features_dict["ndvi_min"],
        ndvi_max           = features_dict["ndvi_max"],
        ndvi_monthly       = features_dict["ndvi_monthly"],
        elevation_mean     = features_dict["elevation_mean"],
        slope_mean         = features_dict["slope_mean"],
        aspect_mean        = features_dict["aspect_mean"],
        ph_mean            = features_dict["ph_mean"],
        clay_pct           = features_dict["clay_pct"],
        sand_pct           = features_dict["sand_pct"],
        silt_pct           = features_dict["silt_pct"],
        organic_carbon     = features_dict["organic_carbon"],
        annual_precip_mm   = features_dict["annual_precip_mm"],
        temp_mean_c        = features_dict["temp_mean_c"],
        temp_min_c         = features_dict["temp_min_c"],
        temp_max_c         = features_dict["temp_max_c"],
        precip_seasonality = features_dict["precip_seasonality"],
        data_source        = features_dict["data_source"],
    )
    db.add(analysis)
    db.flush()

    # 6. Calcular scores para todos los cultivos
    score_results = run_scoring(features_dict)

    crop_score_orm_list = []
    for sr in score_results:
        cs = CropScore(
            analysis_id          = analysis.id,
            crop_id              = sr["crop_id"],
            crop_name            = sr["crop_name"],
            score_total          = sr["score_total"],
            score_breakdown      = sr["score_breakdown"],
            limiting_factors     = sr["limiting_factors"],
            recommendation_level = sr["recommendation_level"],
            explanation          = sr["explanation"],
        )
        db.add(cs)
        crop_score_orm_list.append(cs)

    db.commit()

    # 7. Construir respuesta
    features_schema = TerrainFeatures(**features_dict)
    scores_schema = [
        CropScoreResponse(**sr) for sr in score_results
    ]

    return AnalysisResponse(
        analysis_id  = analysis.id,
        terrain_id   = terrain.id,
        features     = features_schema,
        scores       = scores_schema,
        computed_at  = analysis.computed_at,
        data_source  = analysis.data_source,
    )


@router.get("/{analysis_id}", summary="Obtener análisis por ID")
def get_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Retorna un análisis previamente calculado."""
    from uuid import UUID
    try:
        uid = UUID(analysis_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="ID inválido")

    analysis = db.query(TerrainAnalysis).filter(TerrainAnalysis.id == uid).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado")

    scores = db.query(CropScore).filter(CropScore.analysis_id == uid).all()

    return {
        "analysis_id":  str(analysis.id),
        "terrain_id":   str(analysis.terrain_id),
        "computed_at":  analysis.computed_at.isoformat(),
        "data_source":  analysis.data_source,
        "features": {
            "ndvi_mean":       analysis.ndvi_mean,
            "ndvi_std":        analysis.ndvi_std,
            "elevation_mean":  analysis.elevation_mean,
            "slope_mean":      analysis.slope_mean,
            "ph_mean":         analysis.ph_mean,
            "clay_pct":        analysis.clay_pct,
            "sand_pct":        analysis.sand_pct,
            "temp_mean_c":     analysis.temp_mean_c,
            "annual_precip_mm": analysis.annual_precip_mm,
        },
        "scores": [
            {
                "crop_id":              s.crop_id,
                "crop_name":            s.crop_name,
                "score_total":          s.score_total,
                "score_breakdown":      s.score_breakdown,
                "limiting_factors":     s.limiting_factors,
                "recommendation_level": s.recommendation_level,
                "explanation":          s.explanation,
            }
            for s in sorted(scores, key=lambda x: x.score_total, reverse=True)
        ],
    }
