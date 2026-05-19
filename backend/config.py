from pydantic_settings import BaseSettings
from pathlib import Path
import secrets

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://agrovision:agrovision123@db:5432/agrovision"
    DATA_MODE: str = "mock"
    GEE_PROJECT: str = ""
    AGRONOMY_FILE: Path = BASE_DIR / "data" / "agronomy" / "crops.yaml"
    # API Key para proteger todos los endpoints.
    # Genera una segura con: python -c "import secrets; print(secrets.token_hex(32))"
    # y ponla en .env como API_KEY=<valor>
    API_KEY: str = secrets.token_hex(32)  # fallback aleatorio en dev si no hay .env

    class Config:
        env_file = ".env"

settings = Settings()
