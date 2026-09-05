import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database.base import SessionLocal
from app.errors import AppError
from app.scheduler import scheduler_loop
from app.websocket.manager import manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("evoting")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # FAZA 8 - ConnectionManageru treba referenca na glavni event loop da bi
    # mogao emitirati WS evente iz sinkronih ruta (npr. POST /voting/cast).
    manager.bind_loop(asyncio.get_running_loop())

    # FAZA 9 (dopuna) - pozadinski zadatak za zakazano otvaranje/zatvaranje
    # izbora (app/scheduler.py). Radi SAMO dok ovaj proces radi - vidi
    # napomenu u scheduler.py.
    scheduler_task = asyncio.create_task(scheduler_loop())

    yield

    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="E-Glasanje API", version="0.1.0", lifespan=lifespan)

# --- CORS (FAZA 7, prosireno u Fazi 9) ---------------------------------------
# Frontend (Vite dev server) radi na drugom portu od backenda, pa browser
# bez ovoga blokira sve pozive prema API-ju (CORS policy).
# 5173 = frontend-terminal (Faza 7), 5174 = frontend-admin (Faza 9, fiksni
# port u vite.config.js) - oba mogu raditi istovremeno.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routeri (FAZA 4) -------------------------------------------------------
from app.auth.router import router as auth_router  # noqa: E402
from app.devices.router import bulk_router as devices_bulk_router  # noqa: E402
from app.devices.router import router as devices_router  # noqa: E402
from app.elections.router import router as elections_router  # noqa: E402
from app.stations.router import router as stations_router  # noqa: E402

app.include_router(auth_router)
app.include_router(elections_router)
app.include_router(stations_router)
app.include_router(devices_router)
app.include_router(devices_bulk_router)

# --- Routeri (FAZA 5) -------------------------------------------------------
from app.tokens.router import admin_router as tokens_admin_router  # noqa: E402
from app.tokens.router import bulk_router as tokens_bulk_router  # noqa: E402
from app.tokens.router import device_router as tokens_device_router  # noqa: E402

app.include_router(tokens_admin_router)
app.include_router(tokens_bulk_router)
app.include_router(tokens_device_router)

# --- Routeri (FAZA 6) -------------------------------------------------------
from app.voting.router import router as voting_router  # noqa: E402

app.include_router(voting_router)

# --- Routeri (FAZA 8) -------------------------------------------------------
from app.websocket.router import router as websocket_router  # noqa: E402

app.include_router(websocket_router)

# --- Routeri (FAZA 9 dopuna) ------------------------------------------------
from app.audit.router import router as audit_router  # noqa: E402

app.include_router(audit_router)


# --- Error handling (poglavlje 27) ---------------------------------------
# Frontend nikad ne smije vidjeti sirovu iznimku ili SQL/DB detalj - svaka
# poznata greska ima svoj stabilan error_code, sve nepoznato pada u
# generički SERVER_ERROR bez ikakvog tehničkog sadržaja u odgovoru.


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.warning("APP_ERROR code=%s path=%s", exc.code, request.url.path)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error_code": exc.code, "message": exc.message},
    )


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error("DATABASE_ERROR path=%s error_type=%s", request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"error_code": "DATABASE_ERROR", "message": "Doslo je do greske na serveru."},
    )


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.error("UNHANDLED_ERROR path=%s error_type=%s", request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"error_code": "SERVER_ERROR", "message": "Doslo je do neocekivane greske."},
    )


# --- Health check -----------------------------------------------------------


@app.get("/health")
def health_check():
    """Potvrdjuje da server radi i da postoji zivi konekcija na bazu."""
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        db_status = "OK"
    except SQLAlchemyError:
        db_status = "UNAVAILABLE"

    return {"status": "OK", "database": db_status}
