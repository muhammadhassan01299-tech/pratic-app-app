"""PostgreSQL connection setup.

Prefer separate DB_* variables so passwords containing @, :, /, #, etc.
are handled safely by SQLAlchemy's URL builder.
"""
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# DB_PASSWORD is recommended. URL.create safely quotes special characters.
if os.getenv("DB_PASSWORD") is not None:
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "Ateeb"),
    )
else:
    # Backward compatibility with a single DATABASE_URL setting.
    raw_database_url = os.getenv("DATABASE_URL", "").strip()
    if not raw_database_url:
        raise RuntimeError(
            "Database configuration missing. Add DB_USER, DB_PASSWORD, DB_HOST, "
            "DB_PORT and DB_NAME to the project's .env file."
        )
    try:
        database_url = make_url(raw_database_url)
    except Exception as exc:
        raise RuntimeError(
            "DATABASE_URL is invalid. Prefer DB_* variables in .env; "
            "they safely support special characters in passwords."
        ) from exc

engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
