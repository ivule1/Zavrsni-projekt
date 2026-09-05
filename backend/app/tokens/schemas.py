import uuid

from pydantic import BaseModel


class TokenGenerateRequest(BaseModel):
    count: int | None = None  # ako izostavljeno, koristi se station.registered_voters
    force: bool = False  # dopusti generiranje i ako pool za stanicu vec postoji


class TokenGenerateResponse(BaseModel):
    station_id: uuid.UUID
    count: int
    # sirovi tokeni - prikazuju se SAMO ovdje, jednom, za sluzbenika da ih
    # isprinta/podijeli. U bazi se sprema samo hash (RULE 04).
    tokens: list[str]


class TokenValidateRequest(BaseModel):
    token: str


class TokenValidateResponse(BaseModel):
    valid: bool
    station_id: uuid.UUID


class TokenPoolSummary(BaseModel):
    # FAZA 9 (dopuna) - SAMO brojevi po statusu, nikad sami tokeni (RULE 04) -
    # koristi admin konzola (zadatak #17) da prikaze postoji li vec pool za
    # stanicu i koliko je jos dostupno, bez ponovnog generiranja "na slijepo"
    station_id: uuid.UUID
    total: int
    available: int
    used: int


class TokenBulkGenerateRequest(BaseModel):
    # FAZA 9 (dopuna) - None = generiraj pool za SVAKO AKTIVNO biraliste
    station_ids: list[uuid.UUID] | None = None
    count: int | None = None  # po stanici; ako izostavljeno, station.registered_voters
    force: bool = False  # generiraj i za stanice koje vec imaju pool


class TokenBulkStationResult(BaseModel):
    station_id: uuid.UUID
    station_code: str
    count: int
    tokens: list[str]


class TokenBulkGenerateResponse(BaseModel):
    generated: list[TokenBulkStationResult]
    # stanice koje su vec imale pool pa su preskocene (force=False)
    skipped_station_ids: list[uuid.UUID]
