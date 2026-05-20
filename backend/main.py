from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from database import init_db
from api.routes import terrain, crops, analysis
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# CVE-6: Rate limiter global por IP.
# Límites aplicados por endpoint en cada router.
limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Iniciando AgroVision API...")
    init_db()
    logger.info("Base de datos lista")
    yield
    logger.info("Cerrando AgroVision API")


app = FastAPI(
    title="AgroVision API",
    description="Plataforma geoespacial de compatibilidad agrícola",
    version="1.0.0",
    lifespan=lifespan,
)

# Registrar el limiter y su handler de error en la app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(terrain.router, prefix="/api/v1/terrain", tags=["Terrenos"])
app.include_router(crops.router,   prefix="/api/v1/crops",   tags=["Cultivos"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Análisis"])


# CVE-10: health sin metadatos operacionales
@app.get("/api/v1/health", tags=["Sistema"])
def health():
    return {"status": "ok"}
