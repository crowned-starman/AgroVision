"""
Scoring basado en reglas agronómicas.
Usa funciones trapezoidales para cada dimensión del cultivo.
"""
import logging
from simpleeval import simple_eval, FeatureNotAvailable, InvalidExpression

logger = logging.getLogger(__name__)


def trapezoidal_score(value: float, min_v: float, opt_min: float,
                      opt_max: float, max_v: float) -> float:
    """
    Retorna score 0.0-1.0 según posición del valor en el rango del cultivo.

    1.0 ─────────────────┐           ┌──────────
                         │           │
    0.0 ─────────────────┘           └──────────
           min_v    opt_min      opt_max    max_v
    """
    if value <= min_v or value >= max_v:
        return 0.0
    if opt_min <= value <= opt_max:
        return 1.0
    if value < opt_min:
        return (value - min_v) / (opt_min - min_v)
    return (max_v - value) / (max_v - opt_max)


def _check_limiting_factors(features: dict, crop: dict) -> list[dict]:
    """
    Evalúa factores limitantes definidos en el YAML.
    Retorna lista de factores activos con severidad.
    """
    active = []
    for factor in crop.get("limiting_factors", []):
        condition = factor["condition"]
        triggered = False

        # Evaluación segura de condiciones del YAML mediante simpleeval.
        # A diferencia de eval(), simpleeval solo permite expresiones
        # aritméticas y comparaciones — sin imports, atributos ni llamadas
        # a funciones arbitrarias.
        try:
            ctx = {k: v for k, v in features.items() if isinstance(v, (int, float))}
            result = simple_eval(condition, names=ctx)
            triggered = bool(result)
        except (FeatureNotAvailable, InvalidExpression) as e:
            logger.error(
                f"Condición no permitida en cultivo '{crop.get('id', '?')}': "
                f"'{condition}' — {e}"
            )
            continue
        except Exception as e:
            logger.warning(f"Error evaluando condición '{condition}': {e}")
            continue

        if triggered:
            active.append({
                "name":     factor["name"],
                "severity": factor["severity"],
                "message":  factor.get("message", f"Condición limitante: {condition}"),
            })

    return active


def score_crop(features: dict, crop: dict) -> dict:
    """
    Calcula el score de compatibilidad para un cultivo.

    Returns:
        {
          score: float,
          breakdown: {dim: score},
          limiting_factors: [...],
          critical_violation: bool
        }
    """
    req = crop["requirements"]
    breakdown = {}
    weighted_sum = 0.0
    total_weight = 0.0

    # ── Temperatura ───────────────────────────────────────────────────
    if "temperature" in req:
        t = req["temperature"]
        s = trapezoidal_score(
            features["temp_mean_c"],
            t["min_c"], t["optimal_min_c"], t["optimal_max_c"], t["max_c"]
        )
        w = t.get("weight", 0.2)
        breakdown["temperatura"] = round(s, 3)
        weighted_sum += s * w
        total_weight += w

    # ── Precipitación ─────────────────────────────────────────────────
    if "precipitation" in req:
        p = req["precipitation"]
        s = trapezoidal_score(
            features["annual_precip_mm"],
            p["annual_min_mm"], p["annual_optimal_mm"],
            p["annual_optimal_mm"] * 1.1, p["annual_max_mm"]
        )
        w = p.get("weight", 0.20)
        breakdown["precipitacion"] = round(s, 3)
        weighted_sum += s * w
        total_weight += w

    # ── pH del suelo ──────────────────────────────────────────────────
    if "soil_ph" in req:
        ph = req["soil_ph"]
        s = trapezoidal_score(
            features["ph_mean"],
            ph["min"], ph["optimal_min"], ph["optimal_max"], ph["max"]
        )
        w = ph.get("weight", 0.20)
        breakdown["ph_suelo"] = round(s, 3)
        weighted_sum += s * w
        total_weight += w

    # ── NDVI ──────────────────────────────────────────────────────────
    if "ndvi_baseline" in req:
        nb = req["ndvi_baseline"]
        min_v = nb.get("min_viable", 0.1)
        s = min(1.0, (features["ndvi_mean"] - min_v) / max(0.01, 0.8 - min_v))
        s = max(0.0, s)
        w = nb.get("weight", 0.15)
        breakdown["ndvi"] = round(s, 3)
        weighted_sum += s * w
        total_weight += w

    # ── Pendiente ─────────────────────────────────────────────────────
    if "slope" in req:
        sl = req["slope"]
        max_deg = sl.get("max_degrees", 15)
        s = max(0.0, 1.0 - features["slope_mean"] / max_deg)
        s = min(1.0, s)
        w = sl.get("weight", 0.10)
        breakdown["pendiente"] = round(s, 3)
        weighted_sum += s * w
        total_weight += w

    # ── Textura del suelo ─────────────────────────────────────────────
    if "soil_texture" in req:
        st = req["soil_texture"]
        preferred = st.get("preferred", [])
        texture_class = features.get("texture_class", "")
        # Mapeo simplificado de clase a categoría
        texture_map = {
            "arcilloso":       "clay",
            "arenoso":         "sandy_loam",
            "franco":          "loam",
            "franco-arcilloso": "clay_loam",
        }
        mapped = texture_map.get(texture_class, "loam")
        s = 1.0 if mapped in preferred else 0.4
        w = st.get("weight", 0.10)
        breakdown["textura_suelo"] = round(s, 3)
        weighted_sum += s * w
        total_weight += w

    # ── Carbono orgánico ──────────────────────────────────────────────
    if "organic_carbon" in req:
        oc = req["organic_carbon"]
        s = trapezoidal_score(
            features["organic_carbon"],
            oc["min"], oc["optimal_min"], oc["optimal_max"], oc["max"]
        )
        w = oc.get("weight", 0.05)
        breakdown["carbono_organico"] = round(s, 3)
        weighted_sum += s * w
        total_weight += w

    # ── Score final ───────────────────────────────────────────────────
    final_score = weighted_sum / max(total_weight, 0.001)

    # ── Factores limitantes ───────────────────────────────────────────
    limiting_factors = _check_limiting_factors(features, crop)
    critical_violation = any(f["severity"] == "critical" for f in limiting_factors)

    # Penalización por factores limitantes de alta severidad
    high_count = sum(1 for f in limiting_factors if f["severity"] == "high")
    final_score = final_score * max(0.0, 1.0 - 0.25 * high_count)

    if critical_violation:
        final_score = 0.0

    return {
        "score":              round(final_score, 4),
        "breakdown":          breakdown,
        "limiting_factors":   limiting_factors,
        "critical_violation": critical_violation,
    }
