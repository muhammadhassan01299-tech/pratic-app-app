import os
import re
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine
from app.models import User

PROJECT_ROOT = Path(__file__).resolve().parents[1]
STATIC_DIR = PROJECT_ROOT / "app" / "static"
load_dotenv(PROJECT_ROOT / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    # Convenient local-only fallback; set a 32+ character key in .env.
    SECRET_KEY = "local-development-only-change-this-secret-key-2026"
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
password_hash = PasswordHash.recommended()


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except SQLAlchemyError as exc:
        raise RuntimeError(
            "Could not initialize PostgreSQL. Check that PostgreSQL is running, "
            "the database exists, and DB_* values in .env are correct. "
            f"Details: {exc}"
        ) from exc
    yield


app = FastAPI(title="Glossy Login | FastAPI + PostgreSQL", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class SignupPayload(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class LoginPayload(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=1, max_length=128)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def normalize_email(email: str) -> str:
    value = email.strip().lower()
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
        raise HTTPException(status_code=422, detail="Please enter a valid email address.")
    return value


def make_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": str(user.id), "exp": expires}, SECRET_KEY, algorithm=ALGORITHM)


def public_user(user: User) -> dict:
    return {"id": user.id, "full_name": user.full_name, "email": user.email}


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok", "app": "Luma Login"}


@app.get("/db-check")
def db_check():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar_one()
        return {"status": "connected", "database_test": result,
                "message": "FastAPI successfully connected to PostgreSQL!"}
    except SQLAlchemyError:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL connection failed. Check PostgreSQL service, database name, username and password in .env.",
        )


@app.post("/api/auth/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupPayload, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    full_name = payload.full_name.strip()
    if len(full_name) < 2:
        raise HTTPException(status_code=422, detail="Please enter your full name.")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists. Please sign in.")

    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash.hash(payload.password),
    )
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists. Please sign in.")
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Could not save your account. Check the database connection.")

    return {"message": "Your account has been created.", "access_token": make_token(user),
            "token_type": "bearer", "user": public_user(user)}


@app.post("/api/auth/login")
def login(payload: LoginPayload, db: Session = Depends(get_db)):
    email = normalize_email(payload.email)
    user = db.query(User).filter(User.email == email).first()
    if not user or not password_hash.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect.")

    user.last_login_at = datetime.now(timezone.utc)
    user.login_count = (user.login_count or 0) + 1
    try:
        db.commit()
        db.refresh(user)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(status_code=503, detail="Login succeeded but account activity could not be updated.")

    return {"message": "Welcome back!", "access_token": make_token(user),
            "token_type": "bearer", "user": public_user(user)}


@app.get("/api/auth/me")
def me(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Please sign in.")
    try:
        token = authorization.split(" ", 1)[1].strip()
        token_payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(token_payload.get("sub", "0"))
    except (JWTError, ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Your session has expired. Please sign in again.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Account not found.")
    return {"id": user.id, "full_name": user.full_name, "email": user.email,
            "created_at": user.created_at, "last_login_at": user.last_login_at,
            "login_count": user.login_count}
