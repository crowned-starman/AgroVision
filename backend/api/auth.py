"""
Dependencia de autenticación por API Key.

Uso en cualquier router:
    from api.auth import require_api_key

    @router.get("/", dependencies=[Depends(require_api_key)])
    def mi_endpoint(): ...
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from config import settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str | None = Security(_api_key_header)) -> None:
    """
    Valida que el header X-API-Key coincida con settings.API_KEY.
    Lanza HTTP 401 si falta el header y HTTP 403 si la clave es incorrecta.
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key requerida. Incluye el header: X-API-Key: <tu_clave>",
        )
    # Comparación en tiempo constante para evitar timing attacks
    import hmac
    if not hmac.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key inválida",
        )
