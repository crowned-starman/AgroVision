from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://agrovision:agrovision123@db:5432/agrovision"
    DATA_MODE: str = "mock"
    GEE_PROJECT: str = ""
    AGRONOMY_FILE: Path = BASE_DIR / "data" / "agronomy" / "crops.yaml"

    class Config:
        env_file = ".env"

settings = Settings()
