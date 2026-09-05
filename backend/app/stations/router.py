import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import log_event
from app.auth.dependencies import get_current_admin_id
from app.database.base import get_db
from app.database.models import PollingStation
from app.errors import AppError, EmptyBulkRequestError
from app.stations.schemas import (
    StationBulkCreate,
    StationBulkResult,
    StationCreate,
    StationOut,
)

router = APIRouter(
    prefix="/stations",
    tags=["stations"],
    dependencies=[Depends(get_current_admin_id)],
)


class StationCodeTakenError(AppError):
    def __init__(self):
        super().__init__("STATION_CODE_TAKEN", "Sifra biratckog mjesta vec postoji.", status_code=409)


@router.post("", response_model=StationOut, status_code=201)
def create_station(
    payload: StationCreate,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    station = PollingStation(
        code=payload.code,
        name=payload.name,
        location=payload.location,
        zupanija=payload.zupanija,
        registered_voters=payload.registered_voters,
    )
    db.add(station)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise StationCodeTakenError()

    log_event(db, "STATION_REGISTERED", admin_user_id=admin_id, station_id=station.id)
    db.commit()
    db.refresh(station)
    return station


@router.get("", response_model=list[StationOut])
def list_stations(db: Session = Depends(get_db)):
    return db.query(PollingStation).order_by(PollingStation.code).all()


@router.post("/bulk", response_model=StationBulkResult, status_code=201)
def bulk_create_stations(
    payload: StationBulkCreate,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    """FAZA 9 (dopuna) - generički bulk-import biračkih mjesta (zadatak
    #15, stavka 4 dogovorenog plana). Odvojeno od seed migracije - ovo je
    za buduće ručno dodavanje (npr. CSV kroz admin konzolu, zadatak #17).

    Namjerno NE puca na prvom sudaru sifre - postojece/duplicirane sifre
    se preskoce i prijave u odgovoru, ostatak se svejedno upise (poglavlje
    27 - admin dobiva jasan, upotrebljiv rezultat umjesto gole 409 greske
    usred liste od stotinjak redaka).
    """
    if not payload.stations:
        raise EmptyBulkRequestError()

    requested_codes = [item.code for item in payload.stations]
    existing_codes = {
        code
        for (code,) in db.query(PollingStation.code).filter(PollingStation.code.in_(requested_codes))
    }

    created: list[PollingStation] = []
    skipped: list[str] = []
    seen_in_payload: set[str] = set()

    for item in payload.stations:
        if item.code in existing_codes or item.code in seen_in_payload:
            skipped.append(item.code)
            continue
        seen_in_payload.add(item.code)
        station = PollingStation(
            code=item.code,
            name=item.name,
            location=item.location,
            zupanija=item.zupanija,
            registered_voters=item.registered_voters,
        )
        db.add(station)
        created.append(station)

    if created:
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise StationCodeTakenError()

    log_event(
        db,
        "STATIONS_BULK_IMPORTED",
        admin_user_id=admin_id,
        metadata={"created_count": len(created), "skipped_count": len(skipped)},
    )
    db.commit()
    for station in created:
        db.refresh(station)

    return StationBulkResult(created=created, skipped_codes=skipped)
