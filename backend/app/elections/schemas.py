import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, field_validator


class ElectionCreate(BaseModel):
    name: str
    # FAZA 9 (dopuna) - opcionalno zakazano automatsko otvaranje/zatvaranje.
    # Kad je scheduled_open_at postavljen, par kljuceva se generira ODMAH
    # (vidi router.create_election) - vidi se u odgovoru kao private_key_pem.
    scheduled_open_at: datetime | None = None
    scheduled_close_at: datetime | None = None

    @field_validator("scheduled_open_at", "scheduled_close_at")
    @classmethod
    def _ensure_utc(cls, value: datetime | None) -> datetime | None:
        # Ako frontend nekad posalje datum/vrijeme BEZ eksplicitne vremenske
        # zone (ne bi trebao - <input type="datetime-local"> se pretvara u
        # UTC preko .toISOString() PRIJE slanja), tretiraj ga kao UTC umjesto
        # da kasnije puca usporedba naive/aware datetime-a u scheduler.py.
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class ElectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    status: str
    created_at: datetime
    opened_at: datetime | None = None
    closed_at: datetime | None = None
    scheduled_open_at: datetime | None = None
    scheduled_close_at: datetime | None = None


class ElectionCreateOut(ElectionOut):
    # postavljeno SAMO ako je scheduled_open_at zatrazen pri kreiranju
    # (kljuc se tad generira odmah - vidi ElectionCreate) - prikazuje se
    # SAMO ovaj put, admin ga mora sacuvati izvan sustava (34.1)
    private_key_pem: str | None = None


class ElectionOpenOut(BaseModel):
    election: ElectionOut
    # Prikazuje se SAMO u ovom odgovoru, jednom - admin ga mora sacuvati
    # izvan sustava (34.1). None ako je izbor bio ZAKAZAN (kljuc je vec
    # prikazan pri kreiranju - vidi ElectionCreateOut) - regeneriranje bi
    # ponistilo vec spremljeni kljuc.
    private_key_pem: str | None = None


class CandidateCreate(BaseModel):
    name: str
    display_order: int = 0


class CandidateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    election_id: uuid.UUID
    name: str
    display_order: int


class CandidateBulkItem(BaseModel):
    name: str
    # ako izostavljeno, dodjeljuje se automatski redom nakon postojecih kandidata
    display_order: int | None = None


class CandidateBulkCreate(BaseModel):
    candidates: list[CandidateBulkItem]


class StationVoteCount(BaseModel):
    station_id: uuid.UUID
    station_code: str
    count: int


class VoteCountsOut(BaseModel):
    election_id: uuid.UUID
    total_votes: int
    stations: list[StationVoteCount]


class TallyRequest(BaseModel):
    # NIKAD se ne sprema - koristi se samo unutar ovog jednog zahtjeva da
    # se dekriptiraju glasovi, pa se odbacuje (34.1)
    private_key_pem: str


class TallyCandidateResult(BaseModel):
    candidate_id: uuid.UUID
    name: str
    count: int


class TallyStationResult(BaseModel):
    # FAZA 9 (dopuna) - rezultat po biralistu (zadatak #16)
    station_id: uuid.UUID
    station_code: str
    station_name: str
    total: int
    by_candidate: list[TallyCandidateResult]


class TallyGroupResult(BaseModel):
    # FAZA 9 (dopuna) - rezultat po zupaniji ILI po NUTS2 regiji (zadatak
    # #16). "group" je naziv zupanije/regije, ili "Dijaspora"/"Nepoznato"
    # za birališta bez (prepoznate) zupanije
    group: str
    total: int
    by_candidate: list[TallyCandidateResult]


class TallyResult(BaseModel):
    election_id: uuid.UUID
    total_votes: int
    integrity_ok: bool
    results: list[TallyCandidateResult]
    by_station: list[TallyStationResult]
    by_zupanija: list[TallyGroupResult]
    by_region: list[TallyGroupResult]


class DeviceVoteCount(BaseModel):
    # FAZA 9 (dopuna) - per-device prikaz (zadatak #16, stavka 6), izvor:
    # audit_logs VOTE_ACCEPTED zapisi za OVAJ izbor
    device_id: uuid.UUID
    device_code: str
    station_id: uuid.UUID
    station_code: str
    count: int


class DeviceVoteCountsOut(BaseModel):
    election_id: uuid.UUID
    total_votes: int
    devices: list[DeviceVoteCount]
