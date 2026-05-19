"""
Motor de scoring principal.
Carga cultivos del YAML, aplica rule scorer a cada uno,
genera explicaciones legibles y ordena resultados.
"""
import yaml
import logging
from pathlib import Path
from modules.scoring.rule_scorer import score_crop
from config import settings

logger = logging.getLogger(__name__)

_agronomy_db: dict | None = None


def _load_agronomy_db() -> dict:
    global _agronomy_db
    if _agronomy_db is not None:
        return _agronomy_db

    path = settings.AGRONOMY_FILE
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    _agronomy_db = {c["id"]: c for c in data["crops"] if c.get("active", True)}
    logger.info(f"Base agronómica cargada: {len(_agronomy_db)} cultivos")
    return _agronomy_db


def _classify(score: float) -> str:
    if score >= 0.75: return "alto"
    if score >= 0.50: return "medio"
    if score >= 0.25: return "bajo"
    return "incompatible"


def _generate_explanation(crop_name: str, level: str,
                           breakdown: dict, limiting_factors: list) -> str:
    """Genera un párrafo breve explicando el score."""
    level_text = {
        "alto":         "es muy compatible con este terreno",
        "medio":        "tiene compatibilidad moderada con este terreno",
        "bajo":         "presenta compatibilidad baja con este terreno",
        "incompatible": "no es viable en este terreno",
    }

    best_dims = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
    worst_dims = [k for k, v in breakdown.items() if v < 0.5]

    explanation = f"{crop_name} {level_text[level]}."

    if best_dims and best_dims[0][1] > 0.7:
        dim_names = {
            "temperatura":      "temperatura",
            "precipitacion":    "precipitación",
            "ph_suelo":         "pH del suelo",
            "ndvi":             "actividad vegetal histórica",
            "pendiente":        "pendiente del terreno",
            "textura_suelo":    "textura del suelo",
            "carbono_organico": "materia orgánica",
        }
        best_name = dim_names.get(best_dims[0][0], best_dims[0][0])
        explanation += f" El factor más favorable es la {best_name}."

    if worst_dims:
        worst_names = [
            {"temperatura": "temperatura", "precipitacion": "precipitación",
             "ph_suelo": "pH", "ndvi": "NDVI", "pendiente": "pendiente",
             "textura_suelo": "textura del suelo",
             "carbono_organico": "materia orgánica"}.get(d, d)
            for d in worst_dims[:2]
        ]
        explanation += f" Factores limitantes: {', '.join(worst_names)}."

    if limiting_factors:
        critical = [f for f in limiting_factors if f["severity"] == "critical"]
        if critical:
            explanation += f" Restricción crítica: {critical[0]['message']}."

    return explanation


def run_scoring(features: dict) -> list[dict]:
    """
    Ejecuta el scoring para todos los cultivos activos.

    Returns:
        Lista de resultados ordenados por score descendente.
    """
    db = _load_agronomy_db()
    results = []

    for crop_id, crop in db.items():
        try:
            result = score_crop(features, crop)
            level = _classify(result["score"])
            explanation = _generate_explanation(
                crop["name"], level,
                result["breakdown"], result["limiting_factors"]
            )

            results.append({
                "crop_id":              crop_id,
                "crop_name":            crop["name"],
                "score_total":          result["score"],
                "score_breakdown":      result["breakdown"],
                "limiting_factors":     result["limiting_factors"],
                "recommendation_level": level,
                "explanation":          explanation,
            })
        except Exception as e:
            logger.error(f"Error scoring cultivo {crop_id}: {e}")
            continue

    results.sort(key=lambda x: x["score_total"], reverse=True)
    return results


def get_all_crops() -> list[dict]:
    """Retorna metadata de todos los cultivos (sin requirements internos)."""
    db = _load_agronomy_db()
    return [
        {
            "id":              c["id"],
            "name":            c["name"],
            "scientific_name": c.get("scientific_name", ""),
            "category":        c.get("category", ""),
            "description":     c.get("description", ""),
        }
        for c in db.values()
    ]
