"""
FAZA 9 (dopuna) - pozadinski zadatak koji svakih CHECK_INTERVAL_SECONDS
provjerava ima li izbora ciji je zakazano vrijeme otvaranja/zatvaranja
proslo, pa ih automatski otvara/zatvara (npr. "otvori u nedjelju u 7
ujutro, zatvori u 19 navecer") - bez ovoga bi netko morao rucno kliknuti
tocno u to vrijeme.

VAZNO OGRANICENJE (akademski prototip, ne prava produkcijska cron infra):
ovaj zadatak radi SAMO dok backend proces neprekidno radi (pokrece se u
app/main.py lifespan). Ako se server ugasi tocno u trenutku kad bi trebao
otvoriti/zatvoriti izbor, to se NECE dogoditi dok se server sljedeci put ne
pokrene - namjerno nema "catch-up" mehanizma (da se izbor ne otvori npr.
sat vremena kasnije bez nadzora, sto bi moglo iznenaditi administratora).

Kljuc za otvaranje se NE generira ovdje - ako je izbor zakazan, kljuc je
vec generiran i prikazan administratoru pri kreiranju izbora (vidi
app/elections/router.py create_election). Ovaj zadatak samo mijenja status.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.audit.service import log_event
from app.database.base import SessionLocal
from app.database.models import Candidate, Election, ElectionStatus
from app.websocket.broadcaster import broadcast_public_event

logger = logging.getLogger("evoting.scheduler")

CHECK_INTERVAL_SECONDS = 20


def _broadcast_election_changed(election: Election) -> None:
    # Ista minimalna poruka kao u app/elections/router.py (namjerno
    # duplicirano ovdje umjesto uvoza iz router.py - izbjegava kruzni uvoz
    # jer bi router.py inace morao uvoziti scheduler.py za registraciju
    # pozadinskog zadatka u main.py).
    broadcast_public_event(
        {
            "type": "election_changed",
            "election_id": str(election.id),
            "status": election.status.value,
        }
    )


def run_due_actions(db: Session) -> None:
    """Izvrsava sve zakazane akcije cije je vrijeme proslo. Izdvojeno iz
    scheduler_loop() da se moze pozvati i izravno u testovima, bez
    cekanja na asyncio.sleep petlju."""
    now = datetime.now(timezone.utc)

    due_to_open = (
        db.query(Election)
        .filter(
            Election.status == ElectionStatus.DRAFT,
            Election.scheduled_open_at.isnot(None),
            Election.scheduled_open_at <= now,
        )
        .all()
    )
    for election in due_to_open:
        candidate_count = db.query(Candidate).filter(Candidate.election_id == election.id).count()
        if candidate_count == 0:
            # Sigurnosna ograda - rucno otvaranje ima admin koji potvrdjuje
            # dijalog ("izbor mora imati barem jednog kandidata"), ali
            # automatsko otvaranje nema nikoga tko bi to primijetio. Ne
            # oznacavamo kao "obradjeno" - probat ce ponovno svaki sljedeci
            # ciklus (CHECK_INTERVAL_SECONDS) dok admin ne doda kandidate ili
            # rucno ne postupi drukcije.
            logger.warning("Zakazano otvaranje izbora %s preskoceno - nema dodanih kandidata.", election.id)
            continue

        election.status = ElectionStatus.OPEN
        election.opened_at = now
        log_event(
            db,
            "ELECTION_OPENED",
            metadata={"election_id": str(election.id), "scheduled": True},
        )
        db.commit()
        db.refresh(election)
        _broadcast_election_changed(election)
        logger.info("Izbor %s automatski otvoren (zakazano vrijeme).", election.id)

    due_to_close = (
        db.query(Election)
        .filter(
            Election.status == ElectionStatus.OPEN,
            Election.scheduled_close_at.isnot(None),
            Election.scheduled_close_at <= now,
        )
        .all()
    )
    for election in due_to_close:
        election.status = ElectionStatus.CLOSED
        election.closed_at = now
        log_event(
            db,
            "ELECTION_CLOSED",
            metadata={"election_id": str(election.id), "scheduled": True},
        )
        db.commit()
        db.refresh(election)
        _broadcast_election_changed(election)
        logger.info("Izbor %s automatski zatvoren (zakazano vrijeme).", election.id)


async def scheduler_loop() -> None:
    while True:
        try:
            db = SessionLocal()
            try:
                run_due_actions(db)
            finally:
                db.close()
        except Exception:
            # Namjerno "guta" gresku i nastavlja petlju - jedan neuspjeli
            # ciklus (npr. privremeni DB prekid) ne smije trajno ugasiti
            # provjeru buducih zakazanih izbora.
            logger.exception("Greska u pozadinskom scheduler zadatku.")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
