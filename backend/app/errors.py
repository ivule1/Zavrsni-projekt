"""
Poznate poslovne greske sustava (poglavlje 27 specifikacije).

Svaka nasljeđuje AppError i nosi stabilan `code` koji frontend koristi da
odluči što prikazati korisniku - nikad se ne prikazuje sirova iznimka ili
SQL/DB detalj (poglavlje 27: "Frontend ne smije prikazivati tehnicke
detalje baze korisniku.").

Ove klase se jos ne koriste u Fazi 3 (osim kostura), popunjavaju se
postupno kroz Faze 4-6 kad nastanu stvarne provjere na koje se odnose.
"""


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class InvalidTokenError(AppError):
    """Token ne postoji u bazi (poglavlje 6, 8, 27)."""

    def __init__(self):
        super().__init__("INVALID_TOKEN", "Token ne postoji.", status_code=404)


class TokenAlreadyUsedError(AppError):
    """Token vec ima status USED - RULE 05 (poglavlje 5, 8, 27)."""

    def __init__(self):
        super().__init__("TOKEN_ALREADY_USED", "Token je vec iskoristen.", status_code=409)


class ElectionNotOpenError(AppError):
    """Pokusaj glasanja/administracije dok election nije u statusu OPEN."""

    def __init__(self):
        super().__init__("ELECTION_NOT_OPEN", "Izbor trenutno nije otvoren.", status_code=409)


class StationOfflineError(AppError):
    """Bircko mjesto se ne javlja (poglavlje 25 - dostupnost)."""

    def __init__(self):
        super().__init__("STATION_OFFLINE", "Bircko mjesto nije dostupno.", status_code=503)


class DeviceNotAuthorizedError(AppError):
    """Device API kljuc nedostaje/neispravan/opozvan (poglavlje 34.2)."""

    def __init__(self):
        super().__init__("DEVICE_NOT_AUTHORIZED", "Uredjaj nije autoriziran.", status_code=401)


class EmptyBulkRequestError(AppError):
    """FAZA 9 (dopuna) - bulk zahtjev bez ijednog elementa, ili filter
    (npr. station_ids) koji ne pogadja nijedan postojeci zapis. Zajednicka
    greska za sve bulk endpointe (stanice/uredjaji/tokeni/kandidati) da se
    ne ponavlja ista provjera po svakom routeru."""

    def __init__(self):
        super().__init__(
            "EMPTY_BULK_REQUEST",
            "Lista za bulk operaciju je prazna ili ne odgovara nijednom postojecem zapisu.",
            status_code=400,
        )
