from fastapi import APIRouter
from modules.scoring.engine import get_all_crops

router = APIRouter()


@router.get("/", summary="Listar cultivos disponibles")
def list_crops():
    return get_all_crops()
