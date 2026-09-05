"""
FAZA 9 zavrsni korak - reset testnih podataka prije predaje profesoru.

Brise SVE izbore, kandidate, glasove, tokene, uredjaje i audit log zapise
(cisto stanje, bez traga testiranja), te SVA biracka mjesta koja NISU dio
sluzbenog seed popisa od 129 (npr. rucno dodana tijekom testiranja poput
"DU-001"). Sluzbenih 129 biralista i admin korisnicki racun OSTAJU netaknuti
- prijava i dalje radi, popis biralista ostaje kompletan.

Trazi eksplicitnu potvrdu (upisi DA) prije ijedne izmjene.

Pokreni iz IVAN_zav/backend foldera:
    .\\venv\\Scripts\\python.exe reset_test_data.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "alembic" / "versions"))

from app.database.base import SessionLocal  # noqa: E402
from app.database.models import (  # noqa: E402
    AuditLog,
    Candidate,
    Device,
    Election,
    PollingStation,
    Vote,
    VoteToken,
)

# Sluzbeni kodovi ucitani IZRAVNO iz seed migracije - jedini izvor istine,
# da se izbjegne rucno prepisivanje/greske u popisu od 129 kodova.
from d70a294c8d77_seed_polling_stations_zupanije import SEED_ROWS  # noqa: E402

OFFICIAL_CODES = {row["code"] for row in SEED_ROWS}


def main():
    db = SessionLocal()
    try:
        election_count = db.query(Election).count()
        candidate_count = db.query(Candidate).count()
        vote_count = db.query(Vote).count()
        token_count = db.query(VoteToken).count()
        device_count = db.query(Device).count()
        audit_count = db.query(AuditLog).count()
        extra_stations = (
            db.query(PollingStation)
            .filter(~PollingStation.code.in_(OFFICIAL_CODES))
            .order_by(PollingStation.code)
            .all()
        )

        print("Bit ce OBRISANO:")
        print(f"  - {election_count} izbora, {candidate_count} kandidata")
        print(f"  - {vote_count} glasova, {token_count} tokena")
        print(f"  - {device_count} registriranih uredjaja")
        print(f"  - {audit_count} audit log zapisa")
        if extra_stations:
            codes = ", ".join(s.code for s in extra_stations)
            print(f"  - {len(extra_stations)} rucno dodanih biralista (izvan sluzbenih 129): {codes}")
        else:
            print("  - 0 rucno dodanih biralista (nema ih izvan sluzbenih 129)")
        print()
        print(f"OSTAJE netaknuto: sluzbenih {len(OFFICIAL_CODES)} biralista + admin korisnicki racun.")
        print()

        confirm = input('Upisi tocno "DA" za potvrdu brisanja (bilo sto drugo odustaje): ')
        if confirm.strip() != "DA":
            print("Odustao/la si - NISTA nije obrisano.")
            return

        db.query(AuditLog).delete(synchronize_session=False)
        db.query(Vote).delete(synchronize_session=False)
        db.query(VoteToken).delete(synchronize_session=False)
        db.query(Device).delete(synchronize_session=False)
        db.query(Candidate).delete(synchronize_session=False)
        db.query(Election).delete(synchronize_session=False)
        for station in extra_stations:
            db.delete(station)
        db.commit()

        remaining = db.query(PollingStation).count()
        print(f"\nGotovo. Baza je sad cista: {remaining} biralista (sva sluzbena), 0 izbora/glasova/uredjaja/tokena.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
