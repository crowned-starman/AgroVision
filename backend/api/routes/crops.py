from fastapi import APIRouter, Depends
from modules.scoring.engine import get_all_crops
from api.auth import require_api_key

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/", summary="Listar cultivos disponibles")
def list_crops():
    return get_all_crops()
