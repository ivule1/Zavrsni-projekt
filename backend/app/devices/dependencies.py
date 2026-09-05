from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.database.models import Device, DeviceStatus
from app.devices.security import hash_device_key
from app.errors import DeviceNotAuthorizedError


def get_current_device(
    db: Session = Depends(get_db),
    x_device_key: str | None = Header(default=None, alias="X-Device-Key"),
) -> Device:
    """FastAPI dependency - provjerava device API kljuc iz 'X-Device-Key' headera.

    Odvojeno od admin JWT-a (Authorization: Bearer ...) - terminal se
    predstavlja svojim vlastitim kljucem (poglavlje 34.2), ne admin tokenom.
    """
    if not x_device_key:
        raise DeviceNotAuthorizedError()

    key_hash = hash_device_key(x_device_key)
    device = db.query(Device).filter(Device.device_key_hash == key_hash).first()

    if device is None or device.status != DeviceStatus.ACTIVE:
        raise DeviceNotAuthorizedError()

    return device
