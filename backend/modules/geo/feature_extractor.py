"""
Orquesta la extracción de features geoespaciales para un terreno.
En modo mock usa mock_client; en modo real usará gee/client.py.
"""
from shapely.geometry import shape, mapping
from shapely.validation import make_valid
from shapely.ops import transform
import pyproj
import logging
from config import settings

logger = logging.getLogger(__name__)


def validate_and_fix_polygon(geojson: dict) -> dict:
    """
    Valida el polígono GeoJSON del frontend.
    Retorna el GeoJSON corregido o lanza ValueError.
    """
    try:
        geom = shape(geojson)
    except Exception as e:
        raise ValueError(f"GeoJSON inválido: {e}")

    if not geom.is_valid:
        logger.warning("Polígono inválido, aplicando corrección automática")
        geom = make_valid(geom)

    if geom.geom_type not in ("Polygon", "MultiPolygon"):
        raise ValueError(f"Se esperaba Polygon, recibido: {geom.geom_type}")

    if geom.is_empty:
        raise ValueError("El polígono está vacío")

    return mapping(geom)


def calculate_area_ha(geojson: dict) -> float:
    """
    Calcula el área en hectáreas usando proyección UTM local.
    """
    geom = shape(geojson)
    lat  = geom.centroid.y
    lon  = geom.centroid.x

    # Determinar zona UTM automáticamente
    utm_zone = int((lon + 180) / 6) + 1
    hemisphere = "north" if lat >= 0 else "south"
    utm_crs = pyproj.CRS(f"+proj=utm +zone={utm_zone} +{hemisphere} +ellps=WGS84")
    wgs84   = pyproj.CRS("EPSG:4326")

    project = pyproj.Transformer.from_crs(wgs84, utm_crs, always_xy=True).transform
    geom_utm = transform(project, geom)

    area_m2 = geom_utm.area
    return round(area_m2 / 10_000, 4)


def extract_features(polygon_geojson: dict) -> dict:
    """
    Punto de entrada principal. Retorna dict completo de features.
    Selecciona fuente de datos según DATA_MODE en config.
    """
    if settings.DATA_MODE == "mock":
        from modules.gee.mock_client import get_environmental_data
        logger.info("Modo mock: generando datos simulados")
    else:
        from modules.gee.client import get_environmental_data
        logger.info("Modo GEE: obteniendo datos satelitales")

    features = get_environmental_data(polygon_geojson)

    # Calcular texture class (informativo)
    clay = features["clay_pct"]
    sand = features["sand_pct"]
    if clay > 40:
        features["texture_class"] = "arcilloso"
    elif sand > 70:
        features["texture_class"] = "arenoso"
    elif clay < 27 and sand < 52:
        features["texture_class"] = "franco"
    else:
        features["texture_class"] = "franco-arcilloso"

    logger.info(
        f"Features extraídas: NDVI={features['ndvi_mean']:.3f}, "
        f"T={features['temp_mean_c']}°C, P={features['annual_precip_mm']}mm"
    )
    return features
