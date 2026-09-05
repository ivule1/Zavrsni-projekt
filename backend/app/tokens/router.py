import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit.service import log_event
from app.auth.dependencies import get_current_admin_id
from app.database.base import get_db
from app.database.models import PollingStation, StationStatus, TokenStatus, VoteToken
from app.devices.dependencies import get_current_device
from app.errors import AppError, EmptyBulkRequestError, InvalidTokenError, TokenAlreadyUsedError
from app.tokens.crypto import generate_raw_token, hash_token
from app.tokens.schemas import (
    TokenBulkGenerateRequest,
    TokenBulkGenerateResponse,
    TokenBulkStationResult,
    TokenGenerateRequest,
    TokenGenerateResponse,
    TokenPoolSummary,
    TokenValidateRequest,
    TokenValidateResponse,
)

# admin_router - upravljanje poolom tokena (zasticeno admin JWT-om)
admin_router = APIRouter(
    prefix="/stations/{station_id}/tokens",
    tags=["tokens"],
    dependencies=[Depends(get_current_admin_id)],
)

# bulk_router - generiranje poolova za vise stanica odjednom (isto zasticeno)
bulk_router = APIRouter(
    prefix="/tokens",
    tags=["tokens"],
    dependencies=[Depends(get_current_admin_id)],
)

# device_router - validacija tokena (zasticeno device API kljucem, poziva terminal)
device_router = APIRouter(prefix="/tokens", tags=["tokens"])


class StationNotFoundError(AppError):
    def __init__(self):
        super().__init__("STATION_NOT_FOUND", "Bircko mjesto ne postoji.", status_code=404)


class TokenPoolAlreadyExistsError(AppError):
    def __init__(self):
        super().__init__(
            "TOKEN_POOL_ALREADY_EXISTS",
            "Pool tokena za ovu stanicu vec postoji. Posalji force=true ako zelis dodati jos.",
            status_code=409,
        )


@admin_router.post("/generate", response_model=TokenGenerateResponse, status_code=201)
def generate_tokens(
    station_id: uuid.UUID,
    payload: TokenGenerateRequest,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    station = db.get(PollingStation, station_id)
    if station is None:
        raise StationNotFoundError()

    existing_count = db.query(VoteToken).filter(VoteToken.station_id == station.id).count()
    if existing_count > 0 and not payload.force:
        raise TokenPoolAlreadyExistsError()

    count = payload.count or station.registered_voters
    raw_tokens: list[str] = []

    for _ in range(count):
        raw = generate_raw_token()
        raw_tokens.append(raw)
        db.add(VoteToken(station_id=station.id, token_hash=hash_token(raw), status=TokenStatus.AVAILABLE))

    # RULE 07 - u audit log ide samo broj generiranih tokena, NIKAD sami tokeni
    log_event(db, "TOKEN_POOL_GENERATED", admin_user_id=admin_id, station_id=station.id, metadata={"count": count})
    db.commit()

    return TokenGenerateResponse(station_id=station.id, count=count, tokens=raw_tokens)


@admin_router.get("/summary", response_model=TokenPoolSummary)
def get_token_pool_summary(
    station_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    """FAZA 9 (dopuna) - admin konzola (zadatak #17) treba znati postoji li
    vec pool i koliko je jos dostupno PRIJE nego ponudi "generiraj" gumb -
    vraca samo brojeve (RULE 04), nikad same tokene."""
    station = db.get(PollingStation, station_id)
    if station is None:
        raise StationNotFoundError()

    total = db.query(VoteToken).filter(VoteToken.station_id == station.id).count()
    available = (
        db.query(VoteToken)
        .filter(VoteToken.station_id == station.id, VoteToken.status == TokenStatus.AVAILABLE)
        .count()
    )
    return TokenPoolSummary(station_id=station.id, total=total, available=available, used=total - available)


@bulk_router.post("/bulk-generate", response_model=TokenBulkGenerateResponse, status_code=201)
def bulk_generate_tokens(
    payload: TokenBulkGenerateRequest,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    """FAZA 9 (dopuna) - generira token pool za vise stanica odjednom
    (zadatak #15, stavka 5 dogovorenog plana - bez ovoga bi admin morao
    129 puta rucno zvati POST /stations/{id}/tokens/generate).

    Isti princip kao pojedinacni endpoint: stanica koja vec ima pool se
    preskace osim ako je force=true (RULE 05 - token je trajno jednokratan,
    pa se pool ne regenerira nehotice preko postojecih tokena).
    """
    query = db.query(PollingStation)
    if payload.station_ids is not None:
        if not payload.station_ids:
            raise EmptyBulkRequestError()
        query = query.filter(PollingStation.id.in_(payload.station_ids))
    else:
        query = query.filter(PollingStation.status == StationStatus.ACTIVE)
    stations = query.order_by(PollingStation.code).all()

    if not stations:
        raise EmptyBulkRequestError()

    existing_counts: dict[uuid.UUID, int] = dict(
        db.query(VoteToken.station_id, func.count(VoteToken.id))
        .filter(VoteToken.station_id.in_([s.id for s in stations]))
        .group_by(VoteToken.station_id)
        .all()
    )

    generated: list[TokenBulkStationResult] = []
    skipped: list[uuid.UUID] = []

    for station in stations:
        if existing_counts.get(station.id, 0) > 0 and not payload.force:
            skipped.append(station.id)
            continue

        count = payload.count or station.registered_voters
        raw_tokens: list[str] = []
        for _ in range(count):
            raw = generate_raw_token()
            raw_tokens.append(raw)
            db.add(VoteToken(station_id=station.id, token_hash=hash_token(raw), status=TokenStatus.AVAILABLE))

        log_event(
            db,
            "TOKEN_POOL_GENERATED",
            admin_user_id=admin_id,
            station_id=station.id,
            metadata={"count": count, "bulk": True},
        )
        generated.append(TokenBulkStationResult(station_id=station.id, station_code=station.code, count=count, tokens=raw_tokens))

    db.commit()
    return TokenBulkGenerateResponse(generated=generated, skipped_station_ids=skipped)


@device_router.post("/validate", response_model=TokenValidateResponse)
def validate_token(
    payload: TokenValidateRequest,
    db: Session = Depends(get_db),
    device=Depends(get_current_device),
):
    """Poziva terminal kad birac unese kljuc (poglavlje 8, korak 5-6).

    Namjerno ne mijenja status tokena - samo potvrdjuje da je valjan i
    dostupan. Stvarna AVAILABLE->USED tranzicija dogadja se atomicno tek
    zajedno sa spremanjem glasa (Faza 6, RULE 06).
    """
    token_hash = hash_token(payload.token)
    vote_token = db.query(VoteToken).filter(VoteToken.token_hash == token_hash).first()

    if vote_token is None or vote_token.station_id != device.station_id:
        # token ne postoji ILI pripada drugoj stanici - identicna reakcija,
        # ne otkrivamo koji je slucaj (poglavlje 27 - frontend ne dobiva detalje)
        log_event(db, "INVALID_TOKEN_ATTEMPT", station_id=device.station_id, device_id=device.id)
        db.commit()
        raise InvalidTokenError()

    if vote_token.status != TokenStatus.AVAILABLE:
        log_event(db, "TOKEN_ALREADY_USED_ATTEMPT", station_id=device.station_id, device_id=device.id)
        db.commit()
        raise TokenAlreadyUsedError()

    log_event(db, "TOKEN_VALIDATION_SUCCESS", station_id=device.station_id, device_id=device.id)
    db.commit()

    return TokenValidateResponse(valid=True, station_id=vote_token.station_id)
