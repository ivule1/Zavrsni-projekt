import uuid

from pydantic import BaseModel, ConfigDict


class DeviceCreate(BaseModel):
    device_code: str


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    station_id: uuid.UUID
    device_code: str
    status: str


class DeviceCreatedOut(BaseModel):
    device: DeviceOut
    # prikazuje se SAMO ovdje, jednom - sprema se samo hash (34.2)
    api_key: str


class DeviceBulkRequest(BaseModel):
    # FAZA 9 (dopuna) - None = registriraj po jedan uredjaj na SVAKO
    # AKTIVNO biralište (npr. odmah nakon seed migracije, zadatak #15,
    # stavka 5 dogovorenog plana). Ako je zadano, registrira samo na
    # navedenim stanicama.
    station_ids: list[uuid.UUID] | None = None
    # ako stanica vec ima >=1 uredjaj, preskoci je (idempotentan "jedan
    # klik" - siguran za ponovno pokretanje bez dupliciranja uredjaja)
    skip_existing: bool = True


class DeviceBulkItem(BaseModel):
    station_id: uuid.UUID
    station_code: str
    device: DeviceOut
    api_key: str


class DeviceBulkResult(BaseModel):
    created: list[DeviceBulkItem]
    # stanice koje su vec imale uredjaj pa su preskocene (skip_existing=True)
    skipped_station_ids: list[uuid.UUID]
