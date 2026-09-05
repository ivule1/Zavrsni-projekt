import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.audit.service import log_event
from app.auth.dependencies import get_current_admin_id
from app.database.base import get_db
from app.database.models import Device, PollingStation, StationStatus
from app.devices.schemas import (
    DeviceBulkItem,
    DeviceBulkRequest,
    DeviceBulkResult,
    DeviceCreate,
    DeviceCreatedOut,
    DeviceOut,
)
from app.devices.security import generate_device_api_key, hash_device_key
from app.errors import AppError, EmptyBulkRequestError

router = APIRouter(
    prefix="/stations/{station_id}/devices",
    tags=["devices"],
    dependencies=[Depends(get_current_admin_id)],
)

# FAZA 9 (dopuna) - bulk registracija uredjaja NIJE vezana uz jednu stanicu
# (moze pokriti sve stanice odjednom), pa treba vlastiti prefiks umjesto
# /stations/{station_id}/devices.
bulk_router = APIRouter(
    prefix="/devices",
    tags=["devices"],
    dependencies=[Depends(get_current_admin_id)],
)


class StationNotFoundError(AppError):
    def __init__(self):
        super().__init__("STATION_NOT_FOUND", "Bircko mjesto ne postoji.", status_code=404)


class DeviceCodeTakenError(AppError):
    def __init__(self):
        super().__init__("DEVICE_CODE_TAKEN", "Sifra uredjaja vec postoji.", status_code=409)


@router.get("", response_model=list[DeviceOut])
def list_devices(station_id: uuid.UUID, db: Session = Depends(get_db)):
    # FAZA 9 - admin dashboard treba popis uredjaja po biralistu
    station = db.get(PollingStation, station_id)
    if station is None:
        raise StationNotFoundError()
    return db.query(Device).filter(Device.station_id == station_id).order_by(Device.device_code).all()


@router.post("", response_model=DeviceCreatedOut, status_code=201)
def register_device(
    station_id: uuid.UUID,
    payload: DeviceCreate,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    station = db.get(PollingStation, station_id)
    if station is None:
        raise StationNotFoundError()

    raw_key = generate_device_api_key()
    device = Device(
        station_id=station.id,
        device_code=payload.device_code,
        device_key_hash=hash_device_key(raw_key),
    )
    db.add(device)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise DeviceCodeTakenError()

    log_event(db, "DEVICE_REGISTERED", admin_user_id=admin_id, station_id=station.id, device_id=device.id)
    db.commit()
    db.refresh(device)

    return DeviceCreatedOut(device=device, api_key=raw_key)


@bulk_router.post("/bulk-register", response_model=DeviceBulkResult, status_code=201)
def bulk_register_devices(
    payload: DeviceBulkRequest,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    """FAZA 9 (dopuna) - jedan-klik registracija uredjaja na vise stanica
    odjednom (zadatak #15, stavka 5 dogovorenog plana - bez ovoga bi admin
    morao 129 puta rucno zvati POST /stations/{id}/devices).

    NAMJERNO ne mijenja princip iz poglavlja 34.2 - uredjaj se i dalje mora
    EKSPLICITNO registrirati od strane admina (ovaj poziv JEST ta eksplicitna
    admin akcija, samo odjednom za vise stanica), nikad se ne registrira sam
    otvaranjem stranice terminala.
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
        db.query(Device.station_id, func.count(Device.id))
        .filter(Device.station_id.in_([s.id for s in stations]))
        .group_by(Device.station_id)
        .all()
    )

    created: list[DeviceBulkItem] = []
    skipped: list[uuid.UUID] = []

    for station in stations:
        existing = existing_counts.get(station.id, 0)
        if existing > 0 and payload.skip_existing:
            skipped.append(station.id)
            continue

        raw_key = generate_device_api_key()
        device = Device(
            station_id=station.id,
            device_code=f"{station.code}-DEV{existing + 1}",
            device_key_hash=hash_device_key(raw_key),
        )
        db.add(device)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise DeviceCodeTakenError()

        log_event(
            db,
            "DEVICE_REGISTERED",
            admin_user_id=admin_id,
            station_id=station.id,
            device_id=device.id,
            metadata={"bulk": True},
        )
        created.append(
            DeviceBulkItem(
                station_id=station.id,
                station_code=station.code,
                device=DeviceOut.model_validate(device),
                api_key=raw_key,
            )
        )

    db.commit()
    return DeviceBulkResult(created=created, skipped_station_ids=skipped)
