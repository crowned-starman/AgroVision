"""
Mock de Google Earth Engine.

Genera datos ambientales realistas usando el centroide del polígono
como semilla determinista. El mismo polígono siempre da los mismos
resultados; polígonos distintos dan resultados distintos.

Cuando GEE esté disponible, este módulo se reemplaza por gee/client.py
sin cambiar ningún otro archivo.
"""
import hashlib
import math
import numpy as np
from shapely.geometry import shape


def _seed_from_polygon(geojson: dict) -> int:
    """Genera un entero determinista desde las coordenadas del polígono."""
    coords_str = str(geojson.get("coordinates", ""))
    return int(hashlib.md5(coords_str.encode()).hexdigest(), 16) % (2**31)


def _get_centroid(geojson: dict) -> tuple[float, float]:
    """Retorna (lat, lon) del centroide del polígono."""
    geom = shape(geojson)
    centroid = geom.centroid
    return centroid.y, centroid.x  # lat, lon


def _latitude_climate(lat: float) -> dict:
    """
    Estima rangos climáticos base según latitud.
    Simula la variación tropical (lat~0) vs templada (lat~25-35).
    """
    abs_lat = abs(lat)

    if abs_lat < 10:          # tropical
        temp_mean = 26.0
        temp_range = 5.0
        precip = 1800.0
    elif abs_lat < 20:        # subtropical húmedo
        temp_mean = 24.0
        temp_range = 10.0
        precip = 1200.0
    elif abs_lat < 30:        # subtropical (México central)
        temp_mean = 20.0
        temp_range = 14.0
        precip = 900.0
    else:                     # templado
        temp_mean = 15.0
        temp_range = 18.0
        precip = 700.0

    return {
        "temp_mean": temp_mean,
        "temp_range": temp_range,
        "precip": precip,
    }


def get_environmental_data(polygon_geojson: dict) -> dict:
    """
    Simula el retorno de GEE + SoilGrids + Open-Meteo.

    Returns:
        dict con todas las features ambientales del terreno.
    """
    seed = _seed_from_polygon(polygon_geojson)
    rng = np.random.default_rng(seed)
    lat, lon = _get_centroid(polygon_geojson)
    climate_base = _latitude_climate(lat)

    # ── NDVI ──────────────────────────────────────────────────────────
    ndvi_mean = float(rng.uniform(0.15, 0.75))
    ndvi_std  = float(rng.uniform(0.05, 0.20))
    ndvi_min  = max(0.0, ndvi_mean - rng.uniform(0.15, 0.35))
    ndvi_max  = min(0.95, ndvi_mean + rng.uniform(0.10, 0.25))

    # Serie mensual con estacionalidad realista (sinusoidal + ruido)
    base_month = rng.integers(2, 8)   # mes de pico de vegetación
    ndvi_monthly = []
    for month in range(12):
        seasonal = math.sin(2 * math.pi * (month - base_month) / 12)
        val = ndvi_mean + 0.12 * seasonal + rng.normal(0, 0.03)
        ndvi_monthly.append(round(float(np.clip(val, 0.0, 0.95)), 3))

    # ── Topografía (SRTM) ──────────────────────────────────────────────
    # Elevación varía con latitud para simular altiplanos mexicanos
    elev_base = 1500 if 15 < lat < 25 else 500
    elevation_mean = float(rng.uniform(elev_base * 0.5, elev_base * 1.8))
    slope_mean     = float(rng.uniform(0.5, 18.0))
    aspect_mean    = float(rng.uniform(0, 360))

    # ── Suelo (SoilGrids) ─────────────────────────────────────────────
    clay_pct       = float(rng.uniform(10, 55))
    sand_pct       = float(rng.uniform(10, 60))
    silt_pct       = float(np.clip(100 - clay_pct - sand_pct, 5, 60))
    ph_mean        = float(rng.uniform(5.0, 8.2))
    organic_carbon = float(rng.uniform(0.5, 4.5))

    # ── Clima (ERA5 / Open-Meteo) ──────────────────────────────────────
    t_noise        = float(rng.normal(0, 1.5))
    temp_mean_c    = round(climate_base["temp_mean"] + t_noise, 1)
    temp_range     = climate_base["temp_range"]
    temp_min_c     = round(temp_mean_c - temp_range / 2, 1)
    temp_max_c     = round(temp_mean_c + temp_range / 2, 1)

    precip_noise       = float(rng.normal(0, 120))
    annual_precip_mm   = round(max(100.0, climate_base["precip"] + precip_noise), 1)
    precip_seasonality = float(rng.uniform(0.2, 0.9))   # cv precipitación mensual

    return {
        "ndvi_mean":          round(ndvi_mean, 3),
        "ndvi_std":           round(ndvi_std, 3),
        "ndvi_min":           round(ndvi_min, 3),
        "ndvi_max":           round(ndvi_max, 3),
        "ndvi_monthly":       ndvi_monthly,
        "elevation_mean":     round(elevation_mean, 1),
        "slope_mean":         round(slope_mean, 2),
        "aspect_mean":        round(aspect_mean, 1),
        "ph_mean":            round(ph_mean, 2),
        "clay_pct":           round(clay_pct, 1),
        "sand_pct":           round(sand_pct, 1),
        "silt_pct":           round(silt_pct, 1),
        "organic_carbon":     round(organic_carbon, 2),
        "annual_precip_mm":   annual_precip_mm,
        "temp_mean_c":        temp_mean_c,
        "temp_min_c":         temp_min_c,
        "temp_max_c":         temp_max_c,
        "precip_seasonality": round(precip_seasonality, 3),
        "data_source":        "mock",
    }
