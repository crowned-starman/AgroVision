"""
Cliente real de Google Earth Engine.
Escribe las credenciales desde env var al path esperado por el SDK.
"""
import ee
import os
import json
import logging
import httpx
import numpy as np
from pathlib import Path
from shapely.geometry import shape

logger = logging.getLogger(__name__)
_initialized = False


def _init_gee():
    global _initialized
    if _initialized:
        return

    from config import settings

    # Escribir credenciales al path que espera el SDK de GEE
    cred_dir  = Path("/root/.config/earthengine")
    cred_file = cred_dir / "credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)

    if not cred_file.exists():
        if not settings.GEE_CREDENTIALS_JSON:
            raise ValueError("GEE_CREDENTIALS_JSON no está configurado en .env")
        cred_file.write_text(settings.GEE_CREDENTIALS_JSON)
        logger.info("Credenciales GEE escritas correctamente")

    ee.Initialize(project=settings.GEE_PROJECT)
    _initialized = True
    logger.info(f"GEE inicializado: {settings.GEE_PROJECT}")


def _get_ndvi_stats(geometry: ee.Geometry) -> dict:
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometry)
        .filterDate("2023-01-01", "2024-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(lambda img: img.normalizedDifference(["B8", "B4"])
                           .rename("NDVI")
                           .copyProperties(img, ["system:time_start"]))
    )

    count = collection.size().getInfo()
    logger.info(f"Imágenes Sentinel-2 disponibles: {count}")

    if count < 3:
        logger.warning("Pocas imágenes S2, usando Landsat como fallback")
        collection = (
            ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
            .filterBounds(geometry)
            .filterDate("2023-01-01", "2024-12-31")
            .filter(ee.Filter.lt("CLOUD_COVER", 20))
            .map(lambda img: img.normalizedDifference(["SR_B5", "SR_B4"])
                               .rename("NDVI")
                               .copyProperties(img, ["system:time_start"]))
        )

    composite = collection.mean()
    stats = composite.reduceRegion(
        reducer=(
            ee.Reducer.mean()
            .combine(ee.Reducer.stdDev(), sharedInputs=True)
            .combine(ee.Reducer.min(),    sharedInputs=True)
            .combine(ee.Reducer.max(),    sharedInputs=True)
        ),
        geometry=geometry,
        scale=10,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo()

    def monthly_mean(month):
        month = ee.Number(month)
        return collection.filter(
            ee.Filter.calendarRange(month, month, "month")
        ).mean().set("month", month)

    monthly_vals = ee.ImageCollection(
        ee.List.sequence(1, 12).map(monthly_mean)
    ).aggregate_array("NDVI").getInfo()

    ndvi_mean = stats.get("NDVI_mean") or 0.3
    monthly_clean = [
        round(v, 3) if v is not None else round(ndvi_mean, 3)
        for v in (monthly_vals or [ndvi_mean] * 12)
    ]
    if len(monthly_clean) < 12:
        monthly_clean += [round(ndvi_mean, 3)] * (12 - len(monthly_clean))

    return {
        "ndvi_mean":    round(ndvi_mean, 3),
        "ndvi_std":     round(stats.get("NDVI_stdDev") or 0.05, 3),
        "ndvi_min":     round(stats.get("NDVI_min") or ndvi_mean * 0.6, 3),
        "ndvi_max":     round(stats.get("NDVI_max") or ndvi_mean * 1.3, 3),
        "ndvi_monthly": monthly_clean,
    }


def _get_terrain_stats(geometry: ee.Geometry) -> dict:
    srtm    = ee.Image("USGS/SRTMGL1_003")
    terrain = ee.Terrain.products(srtm)
    stats = terrain.select(["elevation", "slope", "aspect"]).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=30,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo()
    return {
        "elevation_mean": round(stats.get("elevation") or 500.0, 1),
        "slope_mean":     round(stats.get("slope") or 3.0, 2),
        "aspect_mean":    round(stats.get("aspect") or 180.0, 1),
    }


def _get_climate_stats(geometry: ee.Geometry) -> dict:
    era5 = (
        ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
        .filterBounds(geometry)
        .filterDate("2022-01-01", "2024-12-31")
        .select(["temperature_2m", "total_precipitation_sum"])
    )
    stats = era5.mean().reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=10000,
        maxPixels=1e9,
        bestEffort=True,
    ).getInfo()

    temp_k = stats.get("temperature_2m") or 293.15
    temp_c = round(temp_k - 273.15, 1)
    precip_m = stats.get("total_precipitation_sum") or 0.06
    precip_anual = round(precip_m * 1000 * 12, 1)

    temp_stats = era5.select("temperature_2m").reduce(
        ee.Reducer.minMax()
    ).reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=10000,
        bestEffort=True,
    ).getInfo()

    temp_min_k = temp_stats.get("temperature_2m_min") or (temp_k - 7)
    temp_max_k = temp_stats.get("temperature_2m_max") or (temp_k + 7)

    precip_monthly = era5.select("total_precipitation_sum").aggregate_array(
        "total_precipitation_sum"
    ).getInfo() or []

    if len(precip_monthly) > 2:
        arr = [v for v in precip_monthly if v is not None]
        seasonality = round(float(np.std(arr) / (np.mean(arr) + 1e-9)), 3)
    else:
        seasonality = 0.5

    return {
        "temp_mean_c":        temp_c,
        "temp_min_c":         round(temp_min_k - 273.15, 1),
        "temp_max_c":         round(temp_max_k - 273.15, 1),
        "annual_precip_mm":   precip_anual,
        "precip_seasonality": seasonality,
    }


def _get_soil_stats(lat: float, lon: float) -> dict:
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lon": lon, "lat": lat,
        "property": ["phh2o", "clay", "sand", "silt", "soc"],
        "depth": ["0-30cm"],
        "value": ["mean"],
    }
    defaults = {
        "ph_mean": 6.5, "clay_pct": 25.0, "sand_pct": 40.0,
        "silt_pct": 35.0, "organic_carbon": 1.5,
    }
    try:
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        result = {}
        for layer in data.get("properties", {}).get("layers", []):
            name = layer.get("name")
            val  = layer.get("depths", [{}])[0].get("values", {}).get("mean")
            if val is None:
                continue
            if name == "phh2o":   result["ph_mean"]        = round(val / 10, 2)
            elif name == "clay":  result["clay_pct"]       = round(val / 10, 1)
            elif name == "sand":  result["sand_pct"]       = round(val / 10, 1)
            elif name == "silt":  result["silt_pct"]       = round(val / 10, 1)
            elif name == "soc":   result["organic_carbon"] = round(val / 100, 2)
        return {**defaults, **result}
    except Exception as e:
        logger.warning(f"SoilGrids no disponible, usando defaults: {e}")
        return defaults


def get_environmental_data(polygon_geojson: dict) -> dict:
    _init_gee()

    geom_shapely = shape(polygon_geojson)
    centroid     = geom_shapely.centroid
    lat, lon     = centroid.y, centroid.x
    ee_geometry  = ee.Geometry.Polygon(polygon_geojson["coordinates"])

    logger.info(f"Obteniendo datos GEE para ({lat:.4f}, {lon:.4f})")

    ndvi_data    = _get_ndvi_stats(ee_geometry)
    terrain_data = _get_terrain_stats(ee_geometry)
    climate_data = _get_climate_stats(ee_geometry)
    soil_data    = _get_soil_stats(lat, lon)

    logger.info(f"GEE completado: NDVI={ndvi_data['ndvi_mean']:.3f}")

    return {**ndvi_data, **terrain_data, **climate_data, **soil_data, "data_source": "sentinel2"}
