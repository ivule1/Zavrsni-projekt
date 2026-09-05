import random
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.audit.service import log_event
from app.auth.dependencies import get_current_admin_id
from app.database.base import get_db
from app.database.models import AuditLog, Candidate, Device, Election, ElectionStatus, PollingStation, Vote
from app.elections.crypto import generate_election_keypair
from app.elections.regions import NUTS2_REGIONS, get_region
from app.elections.schemas import (
    CandidateBulkCreate,
    CandidateCreate,
    CandidateOut,
    DeviceVoteCount,
    DeviceVoteCountsOut,
    ElectionCreate,
    ElectionCreateOut,
    ElectionOpenOut,
    ElectionOut,
    StationVoteCount,
    TallyCandidateResult,
    TallyGroupResult,
    TallyRequest,
    TallyResult,
    TallyStationResult,
    VoteCountsOut,
)
from app.errors import AppError, EmptyBulkRequestError
from app.voting.crypto import decrypt_vote
from app.voting.integrity import verify_chain
from app.websocket.broadcaster import broadcast_public_event

# poredak kojim se NUTS2 regije prikazuju u by_region rezultatu (isti kao
# na frontendu, "Nepoznato" uvijek zadnje - zupanija je postavljena ali je
# regions.py ne prepoznaje, npr. rucno dodano biraliste s tipfelerom)
_REGION_SORT_ORDER = {name: i for i, name in enumerate(NUTS2_REGIONS)}

router = APIRouter(
    prefix="/elections",
    tags=["elections"],
    dependencies=[Depends(get_current_admin_id)],
)


class ElectionNotFoundError(AppError):
    def __init__(self):
        super().__init__("ELECTION_NOT_FOUND", "Izbor ne postoji.", status_code=404)


class ElectionStateError(AppError):
    def __init__(self, message: str):
        super().__init__("ELECTION_INVALID_STATE", message, status_code=409)


class TallyDecryptionError(AppError):
    """Privatni kljuc ne odgovara javnom kljucu ovog izbora (34.1)."""

    def __init__(self):
        super().__init__(
            "TALLY_DECRYPTION_FAILED",
            "Neispravan privatni kljuc ili osteceni podaci - dekripcija nije uspjela.",
            status_code=422,
        )


def _get_election_or_404(db: Session, election_id: uuid.UUID) -> Election:
    election = db.get(Election, election_id)
    if election is None:
        raise ElectionNotFoundError()
    return election


def _broadcast_election_changed(election: Election) -> None:
    """FAZA 9 (dopuna) - admin dashboard drzi popis izbora u memoriji i
    dohvaca ga samo pri prijavi (poglavlje 14 - 'real-time nadzor'), pa bez
    ovoga otvaranje/zatvaranje/kreiranje izbora na drugom mjestu (npr. kroz
    Swagger dok je dashboard vec otvoren) ne bi bilo vidljivo dok admin
    rucno ne osvjezi stranicu. Poruka je namjerno minimalna (poglavlje 26)
    - koristi se samo kao signal da se ponovno pozove GET /elections (admin)
    odnosno GET /voting/current-election (terminal), ne nosi nikakav sadrzaj
    osim id-a i novog statusa. Ide na broadcast_public_event (ne samo
    admin dashboardu, nego i glasackim terminalima - vidi
    app/websocket/broadcaster.py) jer terminal isto treba znati da provjeri
    je li se nesto promijenilo. Poziva se TEK nakon uspjesnog DB commita
    (poglavlje 15 - isti princip kao i za glasove)."""
    broadcast_public_event(
        {
            "type": "election_changed",
            "election_id": str(election.id),
            "status": election.status.value,
        }
    )


@router.post("", response_model=ElectionCreateOut, status_code=201)
def create_election(
    payload: ElectionCreate,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    if (
        payload.scheduled_open_at is not None
        and payload.scheduled_close_at is not None
        and payload.scheduled_close_at <= payload.scheduled_open_at
    ):
        raise ElectionStateError("Zakazano zatvaranje mora biti nakon zakazanog otvaranja.")

    election = Election(
        name=payload.name,
        status=ElectionStatus.DRAFT,
        scheduled_open_at=payload.scheduled_open_at,
        scheduled_close_at=payload.scheduled_close_at,
    )

    # FAZA 9 (dopuna) - zakazano otvaranje: par kljuceva se generira ODMAH,
    # dok je administrator prisutan da sacuva privatni kljuc (34.1) - stvarno
    # otvaranje u zakazano vrijeme (app/scheduler.py) tad je samo promjena
    # statusa, bez ikoga prisutnog da bi ga inace mogao preuzeti.
    private_pem: str | None = None
    if payload.scheduled_open_at is not None:
        public_pem, private_pem = generate_election_keypair()
        election.public_key = public_pem

    db.add(election)
    db.flush()

    log_event(
        db,
        "ELECTION_CREATED",
        admin_user_id=admin_id,
        metadata={"election_id": str(election.id), "scheduled": private_pem is not None},
    )
    db.commit()
    db.refresh(election)
    _broadcast_election_changed(election)
    return ElectionCreateOut(**ElectionOut.model_validate(election).model_dump(), private_key_pem=private_pem)


@router.get("", response_model=list[ElectionOut])
def list_elections(db: Session = Depends(get_db)):
    # FAZA 9 - admin dashboard treba popis svih izbora (najnoviji prvi) da
    # admin moze odabrati koji nadzire/broji
    return db.query(Election).order_by(Election.created_at.desc()).all()


@router.get("/{election_id}", response_model=ElectionOut)
def get_election(election_id: uuid.UUID, db: Session = Depends(get_db)):
    return _get_election_or_404(db, election_id)


@router.get("/{election_id}/candidates", response_model=list[CandidateOut])
def list_candidates(election_id: uuid.UUID, db: Session = Depends(get_db)):
    _get_election_or_404(db, election_id)
    return (
        db.query(Candidate)
        .filter(Candidate.election_id == election_id)
        .order_by(Candidate.display_order)
        .all()
    )


@router.post("/{election_id}/candidates", response_model=CandidateOut, status_code=201)
def add_candidate(
    election_id: uuid.UUID,
    payload: CandidateCreate,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    election = _get_election_or_404(db, election_id)
    if election.status != ElectionStatus.DRAFT:
        raise ElectionStateError("Kandidati se mogu dodavati samo dok je izbor u statusu DRAFT.")

    candidate = Candidate(election_id=election.id, name=payload.name, display_order=payload.display_order)
    db.add(candidate)

    log_event(
        db,
        "CANDIDATE_ADDED",
        admin_user_id=admin_id,
        metadata={"election_id": str(election.id)},
    )
    db.commit()
    db.refresh(candidate)
    return candidate


@router.post("/{election_id}/candidates/bulk", response_model=list[CandidateOut], status_code=201)
def bulk_add_candidates(
    election_id: uuid.UUID,
    payload: CandidateBulkCreate,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    """FAZA 9 (dopuna) - dodavanje vise kandidata u jednom pozivu (zadatak
    #15, stavka 5 dogovorenog plana) umjesto ponavljanja POST-a za svakog
    kandidata posebno kroz Swagger."""
    if not payload.candidates:
        raise EmptyBulkRequestError()

    election = _get_election_or_404(db, election_id)
    if election.status != ElectionStatus.DRAFT:
        raise ElectionStateError("Kandidati se mogu dodavati samo dok je izbor u statusu DRAFT.")

    existing_max = (
        db.query(func.max(Candidate.display_order)).filter(Candidate.election_id == election.id).scalar() or 0
    )

    created: list[Candidate] = []
    next_order = existing_max + 1
    for item in payload.candidates:
        if item.display_order is not None:
            order = item.display_order
        else:
            order = next_order
            next_order += 1
        candidate = Candidate(election_id=election.id, name=item.name, display_order=order)
        db.add(candidate)
        created.append(candidate)

    db.flush()
    log_event(
        db,
        "CANDIDATE_ADDED",
        admin_user_id=admin_id,
        metadata={"election_id": str(election.id), "bulk": True, "count": len(created)},
    )
    db.commit()
    for candidate in created:
        db.refresh(candidate)
    return created


@router.post("/{election_id}/open", response_model=ElectionOpenOut)
def open_election(
    election_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    election = _get_election_or_404(db, election_id)
    if election.status != ElectionStatus.DRAFT:
        raise ElectionStateError("Samo izbor u statusu DRAFT se moze otvoriti.")

    # Ako je izbor bio ZAKAZAN, public_key je vec postavljen pri kreiranju
    # (a privatni kljuc je vec prikazan administratoru tada - vidi
    # create_election) - ovdje ga NE regeneriramo (to bi ponistilo vec
    # spremljeni kljuc, poglavlje 34.1). Rucno otvaranje PRIJE zakazanog
    # vremena je i dalje moguce (admin promijeni odluku), samo se u tom
    # slucaju NE vraca novi kljuc jer ga je vec dobio.
    private_pem: str | None = None
    if election.public_key is None:
        public_pem, private_pem = generate_election_keypair()
        election.public_key = public_pem
    election.status = ElectionStatus.OPEN
    election.opened_at = datetime.now(timezone.utc)

    log_event(db, "ELECTION_OPENED", admin_user_id=admin_id, metadata={"election_id": str(election.id)})
    db.commit()
    db.refresh(election)
    _broadcast_election_changed(election)

    return ElectionOpenOut(election=election, private_key_pem=private_pem)


@router.post("/{election_id}/close", response_model=ElectionOut)
def close_election(
    election_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    election = _get_election_or_404(db, election_id)
    if election.status != ElectionStatus.OPEN:
        raise ElectionStateError("Samo otvoren izbor se moze zatvoriti.")

    election.status = ElectionStatus.CLOSED
    election.closed_at = datetime.now(timezone.utc)

    log_event(db, "ELECTION_CLOSED", admin_user_id=admin_id, metadata={"election_id": str(election.id)})
    db.commit()
    db.refresh(election)
    _broadcast_election_changed(election)
    return election


@router.get("/{election_id}/vote-counts", response_model=VoteCountsOut)
def get_vote_counts(election_id: uuid.UUID, db: Session = Depends(get_db)):
    """FAZA 9 - pocetno stanje za admin dashboard kad se stranica prvi put
    ucita (prije nego pocnu stizati WS eventi za daljnja azuriranja).
    Namjerno vraca samo agregirane brojeve po biralistu - NIKAD sadrzaj
    glasa niti bilo sto vezano za pojedinacnog biraca (poglavlje 16)."""
    _get_election_or_404(db, election_id)

    rows = (
        db.query(PollingStation.id, PollingStation.code, Vote.id)
        .outerjoin(Vote, (Vote.station_id == PollingStation.id) & (Vote.election_id == election_id))
        .all()
    )

    counts: dict[uuid.UUID, dict] = {}
    for station_id, station_code, vote_id in rows:
        entry = counts.setdefault(station_id, {"station_code": station_code, "count": 0})
        if vote_id is not None:
            entry["count"] += 1

    stations = [
        StationVoteCount(station_id=sid, station_code=data["station_code"], count=data["count"])
        for sid, data in sorted(counts.items(), key=lambda item: item[1]["station_code"])
    ]
    total = sum(s.count for s in stations)

    return VoteCountsOut(election_id=election_id, total_votes=total, stations=stations)


@router.post("/{election_id}/tally", response_model=TallyResult)
def tally_election(
    election_id: uuid.UUID,
    payload: TallyRequest,
    db: Session = Depends(get_db),
    admin_id: uuid.UUID = Depends(get_current_admin_id),
):
    """FAZA 9 - Tally ekran (poglavlje 34.1, 15, 25).

    Admin unosi privatni kljuc koji je dobio SAMO JEDNOM pri otvaranju
    izbora (nikad se ne cuva u sustavu). Kljuc se koristi ISKLJUCIVO unutar
    ovog zahtjeva, u memoriji, i nikad se ne sprema niti loguje.

    Redoslijed:
      1) provjeri lanac integrity_hash-eva NA IZVORNOM (created_at) poretku
      2) tek onda promijesaj glasove nasumicnim redoslijedom prije dekripcije
         (34.1 - "dekripcija u nasumicnom redoslijedu", da rezultati ne
         otkrivaju vremenski poredak glasanja)
    """
    election = _get_election_or_404(db, election_id)
    if election.status != ElectionStatus.CLOSED:
        raise ElectionStateError("Izbor mora biti zatvoren (CLOSED) prije brojanja.")

    votes = db.query(Vote).filter(Vote.election_id == election_id).order_by(Vote.created_at.asc()).all()

    chain_input = [(v.encrypted_vote, v.prev_hash, v.integrity_hash) for v in votes]
    integrity_ok = verify_chain(chain_input, str(election_id))

    shuffled_votes = list(votes)
    random.shuffle(shuffled_votes)

    candidates = db.query(Candidate).filter(Candidate.election_id == election_id).all()
    sorted_candidates = sorted(candidates, key=lambda c: c.display_order)
    counts_by_candidate: dict[uuid.UUID, int] = {c.id: 0 for c in candidates}
    # FAZA 9 (dopuna) - #16: uz globalni zbroj po kandidatu, tijekom ISTOG
    # prolaza (bez ponovne dekripcije) grupiramo i po biralistu - Vote vec
    # nosi station_id (poglavlje 18), pa nema dodatnog upita po glasu
    counts_by_station: dict[uuid.UUID, dict[uuid.UUID, int]] = {}

    for vote in shuffled_votes:
        try:
            plaintext = decrypt_vote(payload.private_key_pem, vote.encrypted_vote)
            candidate_id = uuid.UUID(plaintext["candidate_id"])
        except Exception:
            raise TallyDecryptionError()

        if candidate_id not in counts_by_candidate:
            # kandidat je uklonjen/ne postoji vise - ne smije srusiti citav tally
            counts_by_candidate[candidate_id] = 0
        counts_by_candidate[candidate_id] += 1

        station_counts = counts_by_station.setdefault(vote.station_id, {})
        station_counts[candidate_id] = station_counts.get(candidate_id, 0) + 1

    def _by_candidate_list(counts: dict[uuid.UUID, int]) -> list[TallyCandidateResult]:
        return [
            TallyCandidateResult(candidate_id=c.id, name=c.name, count=counts.get(c.id, 0))
            for c in sorted_candidates
        ]

    results = _by_candidate_list(counts_by_candidate)

    # --- #16: rezultati po biralistu / zupaniji / NUTS2 regiji -------------
    # Dijaspora namjerno NIKAD ne ulazi u zupanijski/regionalni zbroj neke
    # stvarne zupanije/regije - njena "zupanija" je bukvalno "Dijaspora"
    # (vidi seed migraciju), pa je regions.get_region() vraca kao vlastitu
    # kategoriju, odvojenu od svih pravih regija (app/elections/regions.py).
    stations_by_id = {
        s.id: s
        for s in db.query(PollingStation).filter(PollingStation.id.in_(counts_by_station.keys())).all()
    }

    by_station: list[TallyStationResult] = []
    zupanija_counts: dict[str, dict[uuid.UUID, int]] = {}
    region_counts: dict[str, dict[uuid.UUID, int]] = {}

    for station_id, cand_counts in counts_by_station.items():
        station = stations_by_id.get(station_id)
        zupanija = station.zupanija if station else None

        by_station.append(
            TallyStationResult(
                station_id=station_id,
                station_code=station.code if station else "NEPOZNATO",
                station_name=station.name if station else "Nepoznato biralište",
                total=sum(cand_counts.values()),
                by_candidate=_by_candidate_list(cand_counts),
            )
        )

        zup_key = zupanija or "Nepoznato"
        zup_bucket = zupanija_counts.setdefault(zup_key, {})
        for cid, cnt in cand_counts.items():
            zup_bucket[cid] = zup_bucket.get(cid, 0) + cnt

        region_key = get_region(zupanija) or "Nepoznato"
        region_bucket = region_counts.setdefault(region_key, {})
        for cid, cnt in cand_counts.items():
            region_bucket[cid] = region_bucket.get(cid, 0) + cnt

    by_station.sort(key=lambda s: s.station_code)
    by_zupanija = [
        TallyGroupResult(group=z, total=sum(c.values()), by_candidate=_by_candidate_list(c))
        for z, c in sorted(zupanija_counts.items())
    ]
    by_region = [
        TallyGroupResult(group=r, total=sum(c.values()), by_candidate=_by_candidate_list(c))
        for r, c in sorted(region_counts.items(), key=lambda item: _REGION_SORT_ORDER.get(item[0], 999))
    ]

    log_event(
        db,
        "TALLY_PERFORMED",
        admin_user_id=admin_id,
        metadata={"election_id": str(election_id), "total_votes": len(votes), "integrity_ok": integrity_ok},
    )
    db.commit()

    return TallyResult(
        election_id=election_id,
        total_votes=len(votes),
        integrity_ok=integrity_ok,
        results=results,
        by_station=by_station,
        by_zupanija=by_zupanija,
        by_region=by_region,
    )


@router.get("/{election_id}/device-vote-counts", response_model=DeviceVoteCountsOut)
def get_device_vote_counts(election_id: uuid.UUID, db: Session = Depends(get_db)):
    """FAZA 9 (dopuna) - per-device prikaz broja glasova (#16, stavka 6
    dogovorenog plana). Izvor: audit_logs VOTE_ACCEPTED zapisi za OVAJ
    izbor (event_metadata->>'election_id' - vidi app/voting/router.py).

    NAPOMENA: samo glasovi primljeni NAKON ove dopune imaju election_id u
    metapodacima - stariji zapisi (iz vremena prije ove izmjene) nemaju s
    cime usporediti pa se jednostavno ne pojavljuju ovdje (ne pripisuju se
    pogresnom izboru). Ne zahtijeva zatvoren izbor niti privatni kljuc -
    ovo su samo brojevi po uredjaju (RULE 07/09), nema dekripcije."""
    _get_election_or_404(db, election_id)

    rows = (
        db.query(
            AuditLog.device_id,
            Device.device_code,
            AuditLog.station_id,
            PollingStation.code,
            func.count(AuditLog.id),
        )
        .join(Device, Device.id == AuditLog.device_id)
        .join(PollingStation, PollingStation.id == AuditLog.station_id)
        .filter(
            AuditLog.event_type == "VOTE_ACCEPTED",
            AuditLog.event_metadata["election_id"].astext == str(election_id),
        )
        .group_by(AuditLog.device_id, Device.device_code, AuditLog.station_id, PollingStation.code)
        .all()
    )

    devices = [
        DeviceVoteCount(device_id=device_id, device_code=device_code, station_id=station_id, station_code=station_code, count=count)
        for device_id, device_code, station_id, station_code, count in rows
    ]
    devices.sort(key=lambda d: (d.station_code, d.device_code))

    return DeviceVoteCountsOut(
        election_id=election_id,
        total_votes=sum(d.count for d in devices),
        devices=devices,
    )
