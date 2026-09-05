"""
FAZA 9 (dopuna) - admin uvid u sigurnosne/sistemske dogadaje (poglavlje 16:
"Administrator ima pristup... system events, security events").

Namjerno REST + rucno/periodicno osvjezavanje na frontendu, NE WebSocket:
`log_event()` (app/audit/service.py) eksplicitno NE commita - zapisuje se
unutar iste transakcije kao operacija koju biljezi, a commit radi pozivatelj
(desetak razlicitih routera). Emitiranje WS eventa mora ici TEK NAKON commita
(poglavlje 15, RULE 08) - kad bi se to radilo generickim putem odavde, ili bi
se dogadaj mogao emitirati prije nego je transakcija stvarno spremljena, ili
bi trebalo mijenjati sva ta mjesta da posebno javljaju "sad commitaj pa javi
audit". REST dohvat (isti "ucitaj pri otvaranju + gumb Osvjezi" obrazac kao
DeviceVoteCounts) je jednostavniji i bez tog rizika, a podaci nisu toliko
vremenski kriticni kao live broj glasova.
"""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.audit.schemas import AuditLogOut, AuditLogPage
from app.auth.dependencies import get_current_admin_id
from app.database.base import get_db
from app.database.models import AdminUser, AuditLog, PollingStation

router = APIRouter(
    prefix="/audit-logs",
    tags=["audit"],
    dependencies=[Depends(get_current_admin_id)],
)


@router.get("", response_model=AuditLogPage)
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    before: uuid.UUID | None = Query(
        None, description="Vrati zapise starije od zapisa s ovim id-em (paginacija 'ucitaj jos')."
    ),
    event_type: str | None = Query(None, description="Filtriraj po tocnom tipu dogadaja (npr. VOTE_ACCEPTED)."),
    db: Session = Depends(get_db),
):
    query = (
        db.query(AuditLog, AdminUser.username, PollingStation.code)
        .outerjoin(AdminUser, AuditLog.admin_user_id == AdminUser.id)
        .outerjoin(PollingStation, AuditLog.station_id == PollingStation.id)
    )

    if event_type:
        query = query.filter(AuditLog.event_type == event_type)

    if before is not None:
        cursor = db.query(AuditLog.created_at).filter(AuditLog.id == before).scalar()
        if cursor is not None:
            query = query.filter(AuditLog.created_at < cursor)

    # +1 - da znamo ima li jos zapisa iza ove stranice bez drugog upita
    rows = query.order_by(AuditLog.created_at.desc()).limit(limit + 1).all()

    has_more = len(rows) > limit
    rows = rows[:limit]

    items = [
        AuditLogOut(
            id=entry.id,
            event_type=entry.event_type,
            created_at=entry.created_at,
            admin_username=admin_username,
            station_code=station_code,
            device_id=entry.device_id,
            metadata=entry.event_metadata,
        )
        for entry, admin_username, station_code in rows
    ]

    return AuditLogPage(items=items, has_more=has_more)
