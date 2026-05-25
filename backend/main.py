from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from api.routes import terrain, crops, analysis
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


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


@app.get("/api/v1/health", tags=["Sistema"])
def health():
    return {"status": "ok", "version": "1.0.0", "mode": "mock"}
