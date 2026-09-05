import uuid

from pydantic import BaseModel, ConfigDict


class StationCreate(BaseModel):
    code: str
    name: str
    location: str | None = None
    zupanija: str | None = None
    registered_voters: int


class StationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    location: str | None = None
    zupanija: str | None = None
    # FAZA 9 (dopuna) - izvedeno iz zupanije (app/elections/regions.py), ne
    # postoji kao stupac u bazi. None ako zupanija nije popunjena/prepoznata.
    region: str | None = None
    registered_voters: int
    status: str


class StationBulkItem(BaseModel):
    code: str
    name: str
    location: str | None = None
    zupanija: str | None = None
    registered_voters: int = 300


class StationBulkCreate(BaseModel):
    # FAZA 9 (dopuna) - generički bulk-import za buduće ručno dodavanje
    # biračkih mjesta (npr. CSV učitan kroz admin konzolu, zadatak #17) -
    # odvojeno od seed migracije koja pokriva 129 predefiniranih mjesta.
    stations: list[StationBulkItem]


class StationBulkResult(BaseModel):
    created: list[StationOut]
    # sifre koje su preskocene jer vec postoje (u bazi ili duplicirane
    # unutar istog zahtjeva) - operacija ne puca na prvom sudaru, samo
    # preskace i prijavi na kraju
    skipped_codes: list[str]
