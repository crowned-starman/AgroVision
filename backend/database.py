from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from config import settings
import logging

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Habilita PostGIS y crea tablas solo si no existen."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
            conn.commit()
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        if "already exists" in str(e):
            logger.info("Tablas ya existentes, continuando...")
        else:
            raise
