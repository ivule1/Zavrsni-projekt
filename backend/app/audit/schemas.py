import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_type: str
    created_at: datetime
    # "tko" (admin korisnicko ime) i "gdje" (sifra biralista) su izvedeni
    # (join) radi citljivosti u adminskom sucelju - sami po sebi ne krse
    # poglavlje 22 (nisu identitet biraca niti raw token/kljuc).
    admin_username: str | None = None
    station_code: str | None = None
    device_id: uuid.UUID | None = None
    # vec zajamceno bezopasno (poglavlje 22-23) - vidi app/audit/service.py
    metadata: dict | None = None


class AuditLogPage(BaseModel):
    items: list[AuditLogOut]
    # ima li jos starijih zapisa iza zadnjeg vracenog (za "ucitaj jos")
    has_more: bool
