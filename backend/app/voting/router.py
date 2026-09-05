from sqlalchemy import func, update
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.audit.service import log_event
from app.database.base import get_db
from app.database.models import Candidate, Election, ElectionStatus, TokenStatus, Vote, VoteToken
from app.devices.dependencies import get_current_device
from app.errors import AppError, ElectionNotOpenError, InvalidTokenError, TokenAlreadyUsedError
from app.tokens.crypto import hash_token
from app.voting.crypto import encrypt_vote
from app.voting.integrity import compute_integrity_hash
from app.voting.schemas import VoteCastRequest, VoteCastResponse
from app.websocket.broadcaster import broadcast_event

router = APIRouter(prefix="/voting", tags=["voting"])


class CandidateNotFoundError(AppError):
    def __init__(self):
        super().__init__("CANDIDATE_NOT_FOUND", "Kandidat ne postoji za ovaj izbor.", status_code=404)


class ElectionNotFoundError(AppError):
    def __init__(self):
        super().__init__("ELECTION_NOT_FOUND", "Izbor ne postoji.", status_code=404)


@router.get("/current-election")
def get_current_election(db: Session = Depends(get_db), device=Depends(get_current_device)):
    """Poziva terminal da dozna koji je izbor trenutno otvoren i koji su
    kandidati (poglavlje 12 - korak "IZBOR KANDIDATA").

    Namjerno vraca samo ono sto je potrebno za prikaz - bez ikakvih
    osjetljivih podataka (poglavlje 26).
    """
    election = (
        db.query(Election)
        .filter(Election.status == ElectionStatus.OPEN)
        .order_by(Election.opened_at.desc())
        .first()
    )
    if election is None:
        raise ElectionNotOpenError()

    candidates = (
        db.query(Candidate)
        .filter(Candidate.election_id == election.id)
        .order_by(Candidate.display_order)
        .all()
    )

    return {
        "election_id": str(election.id),
        "election_name": election.name,
        "candidates": [{"id": str(c.id), "name": c.name} for c in candidates],
    }


@router.post("/cast", response_model=VoteCastResponse, status_code=201)
def cast_vote(
    payload: VoteCastRequest,
    db: Session = Depends(get_db),
    device=Depends(get_current_device),
):
    """Poglavlje 10 - jedna atomicna transakcija: provjera+potrosnja tokena,
    enkripcija i spremanje glasa - sve ili nista.

    RULE 05 - token moze prijeci samo AVAILABLE -> USED.
    RULE 06 - glas + USED status moraju biti jedna transakcija.
    """
    token_hash = hash_token(payload.token)

    candidate = db.get(Candidate, payload.candidate_id)
    if candidate is None:
        raise CandidateNotFoundError()

    election = db.get(Election, candidate.election_id)
    if election is None:
        raise ElectionNotFoundError()
    if election.status != ElectionStatus.OPEN or not election.public_key:
        raise ElectionNotOpenError()

    # --- atomicna potrosnja tokena (poglavlje 11) ---------------------------
    # UPDATE...WHERE...RETURNING je atomicno na razini retka: ako dva
    # paralelna zahtjeva pokusaju potrositi isti token, samo jedan pogodi
    # WHERE uvjet (status jos AVAILABLE) i dobije redak natrag. Drugi dobije
    # prazan rezultat - to je nas zastitni mehanizam protiv dvostrukog glasanja.
    result = db.execute(
        update(VoteToken)
        .where(
            VoteToken.token_hash == token_hash,
            VoteToken.status == TokenStatus.AVAILABLE,
            VoteToken.station_id == device.station_id,
        )
        .values(status=TokenStatus.USED)
        .returning(VoteToken.id, VoteToken.station_id)
    )
    row = result.first()

    if row is None:
        # dodatni (read-only) upit SAMO da znamo tocnu poruku - ne mijenja nista
        existing = (
            db.query(VoteToken)
            .filter(VoteToken.token_hash == token_hash, VoteToken.station_id == device.station_id)
            .first()
        )
        if existing is None:
            log_event(db, "INVALID_TOKEN_ATTEMPT", station_id=device.station_id, device_id=device.id)
            db.commit()
            raise InvalidTokenError()
        log_event(db, "TOKEN_ALREADY_USED_ATTEMPT", station_id=device.station_id, device_id=device.id)
        db.commit()
        raise TokenAlreadyUsedError()

    _token_id, station_id = row

    # --- lancani integrity hash (34.1) --------------------------------------
    last_vote = (
        db.query(Vote)
        .filter(Vote.election_id == election.id)
        .order_by(Vote.created_at.desc())
        .first()
    )
    prev_hash = last_vote.integrity_hash if last_vote else None

    encrypted_vote = encrypt_vote(election.public_key, candidate.id)
    integrity_hash = compute_integrity_hash(encrypted_vote, prev_hash, str(election.id))

    vote = Vote(
        election_id=election.id,
        station_id=station_id,
        encrypted_vote=encrypted_vote,
        integrity_hash=integrity_hash,
        prev_hash=prev_hash,
    )
    db.add(vote)

    # RULE 07/09 - ni audit log ni (kasniji) WS event ne smiju sadrzavati
    # token, candidate_id niti sadrzaj glasa - samo cinjenica da je primljen.
    # election_id NIJE osjetljiv (nije token/identitet/sadrzaj glasa niti
    # token->vote veza) i FAZA 9 dopuna (#16) ga koristi da admin konzola
    # moze prikazati broj glasova PO UREDJAJU za konkretan izbor umjesto
    # samo ukupno kroz sve izbore ikad odrađene na tom uredjaju.
    log_event(
        db,
        "VOTE_ACCEPTED",
        station_id=device.station_id,
        device_id=device.id,
        metadata={"election_id": str(election.id)},
    )

    db.commit()
    db.refresh(vote)

    # WS event se emitira TEK nakon uspjesnog COMMIT-a (poglavlje 15, RULE 08/09).
    # Poruka je namjerno minimalna (poglavlje 26) - samo tip, izbor, biraliste
    # i agregirani broj glasova ZA TAJ IZBOR na tom biralistu (ne kroz sve
    # izbore ikad - mora se poklapati s GET /elections/{id}/vote-counts koji
    # admin dashboard ucita pri otvaranju, poglavlje 16), NIKAD
    # token/candidate_id/sadrzaj glasa.
    vote_count = (
        db.query(func.count(Vote.id))
        .filter(Vote.station_id == station_id, Vote.election_id == election.id)
        .scalar()
    )
    broadcast_event(
        {
            "type": "vote_count",
            "election_id": str(election.id),
            "station_id": str(device.station_id),
            "count": vote_count,
        }
    )

    return VoteCastResponse(accepted=True, vote_id=vote.id)
