"""
Audit logging (poglavlje 22-23).

VAZNO: `metadata` NIKAD ne smije sadrzavati raw token, token_hash,
identitet biraca, OIB, sadrzaj glasa niti token->vote vezu. Ovo polje
postoji za bezopasan kontekst (npr. election_id, brojcane vrijednosti),
ne za bilo sto sto bi ugrozilo pravila iz poglavlja 22.
"""

import uuid

from sqlalchemy.orm import Session

from app.database.models import AuditLog


def log_event(
    db: Session,
    event_type: str,
    *,
    admin_user_id: uuid.UUID | None = None,
    station_id: uuid.UUID | None = None,
    device_id: uuid.UUID | None = None,
    metadata: dict | None = None,
) -> None:
    entry = AuditLog(
        event_type=event_type,
        admin_user_id=admin_user_id,
        station_id=station_id,
        device_id=device_id,
        event_metadata=metadata,
    )
    db.add(entry)
    # namjerno se NE commita ovdje - poziva se unutar iste transakcije
    # kao i sama operacija koja se logira, commit radi pozivatelj
