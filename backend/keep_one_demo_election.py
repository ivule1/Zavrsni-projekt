"""
Zavrsni korak prije predaje profesoru - zadrzi TOCNO JEDAN izbor kao demo
(da profesor odmah vidi popunjen Tally ekran s rezultatima), a obrisi sve
ostale izbore nastale tijekom razvoja/testiranja.

Sto rade:
  - Prikaze popis SVIH izbora u bazi (naziv, status, broj kandidata, broj
    glasova) i predlozi izbor s najvise glasova kao demo (obicno najbogatiji
    prikaz na Tally grafovima).
  - Nakon tvoje potvrde (upisi DA):
      * SVI OSTALI izbori se brisu (kandidati i glasovi idu s njima -
        ON DELETE CASCADE definiran u shemi, poglavlje 17-21)
      * audit_logs zapisi VEZANI za obrisane izbore (ELECTION_OPENED/
        CLOSED/CREATED, VOTE_ACCEPTED, TALLY_PERFORMED - prepoznati preko
        election_id u metapodacima) se takodjer brisu, da "Sigurnosni i
        sistemski dogadaji" panel u adminu ne prikazuje trag obrisanih
        testnih izbora
      * SVI vote_tokens zapisi se resetiraju (prazni pool) - tokeni NISU
        vezani za izbor (poglavlje 20), pa je ovo neovisno o tome koji se
        izbor zadrzava; ne utjece na vec spremljene glasove zadrzanog
        izbora (Tally cita iskljucivo `votes` tablicu)
      * Uredjaji (devices) koji NISU koristeni za zadrzani izbor se brisu -
        oni koji JESU (imaju VOTE_ACCEPTED audit zapis za zadrzani izbor)
        ostaju, da "Glasovi po uredjaju" panel za taj izbor i dalje radi

Nakon odabira izbora koji se zadrzava, skripta nudi i preimenovanje (npr.
testni naziv poput "Test Skripta Izbor 2" u nesto prezentabilnije za
profesora, poput "Predsjednicki izbori 2026") - Enter zadrzava trenutni
naziv, ili upises novi.

Sluzbenih 129 biralista i admin korisnicki racun OSTAJU netaknuti u oba
slucaja.

Pokreni iz IVAN_zav/backend foldera:
    .\\venv\\Scripts\\python.exe keep_one_demo_election.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database.base import SessionLocal  # noqa: E402
from app.database.models import (  # noqa: E402
    AuditLog,
    Candidate,
    Device,
    Election,
    Vote,
    VoteToken,
)


def main():
    db = SessionLocal()
    try:
        elections = db.query(Election).order_by(Election.created_at).all()
        if not elections:
            print("Nema nijednog izbora u bazi - nema sto zadrzati/brisati.")
            return

        print("Postojeci izbori:\n")
        info = []
        for e in elections:
            candidate_count = db.query(Candidate).filter(Candidate.election_id == e.id).count()
            vote_count = db.query(Vote).filter(Vote.election_id == e.id).count()
            info.append((e, candidate_count, vote_count))

        for i, (e, cand_count, vote_count) in enumerate(info, start=1):
            print(f"  {i}. {e.name}  [{e.status.value}]  - {cand_count} kandidata, {vote_count} glasova")

        recommended_idx = max(range(len(info)), key=lambda i: info[i][2]) + 1
        recommended_name = info[recommended_idx - 1][0].name
        print(f"\nPreporuka (najvise glasova): {recommended_idx}. {recommended_name}")

        choice = input(f"\nKoji izbor zadrzati kao demo? (broj, Enter = preporuceni {recommended_idx}): ").strip()
        keep_idx = int(choice) if choice else recommended_idx
        if keep_idx < 1 or keep_idx > len(info):
            print("Neispravan broj - odustajem, nista nije promijenjeno.")
            return

        keep_election, keep_cand_count, keep_vote_count = info[keep_idx - 1]
        others = [e for e, _, _ in info if e.id != keep_election.id]

        new_name = input(
            f'\nNovi naziv za ovaj izbor (Enter = zadrži "{keep_election.name}"): '
        ).strip()
        if new_name:
            keep_election.name = new_name

        print(f"\nZADRŽAVA SE: \"{keep_election.name}\" ({keep_cand_count} kandidata, {keep_vote_count} glasova)")
        if others:
            print(f"BRIŠE SE ({len(others)} izbora): " + ", ".join(f'"{e.name}"' for e in others))
        else:
            print("Nema drugih izbora za brisanje.")
        token_count = db.query(VoteToken).count()
        print(f"Svi zapisi tokena ({token_count}) se resetiraju na prazan pool (neovisno o izboru).")

        print(
            "\nVAŽNO - provjeri PRIJE potvrde: privatni ključ izbora se prikazuje SAMO JEDNOM,\n"
            "pri otvaranju/kreiranju (poglavlje 34.1) - sustav ga nigdje ne sprema. Ako želiš\n"
            f'profesoru pokazati Tally (dešifriranje) za "{keep_election.name}", provjeri da\n'
            "taj ključ još imaš spremljen NEGDJE IZVAN sustava (npr. .pem datoteka koju si\n"
            "sačuvao/la kad si otvarao/la ovaj izbor). Ako ključ nemaš, biranje drugog izbora\n"
            "za koji ga imaš je jednostavnije nego pokušaj oporavka - ključ se ne može ponovno\n"
            "dohvatiti niti regenerirati a da se ne izgube već izbrojani rezultati."
        )
        print()

        confirm = input('Upiši točno "DA" za potvrdu (bilo što drugo odustaje): ')
        if confirm.strip() != "DA":
            print("Odustao/la si - ništa nije obrisano.")
            return

        other_ids = [e.id for e in others]
        other_ids_str = [str(eid) for eid in other_ids]

        # uredjaji koji su koristeni za zadrzani izbor (imaju VOTE_ACCEPTED
        # audit zapis s election_id zadrzanog izbora u metapodacima) -
        # ovi MORAJU ostati da "Glasovi po uredjaju" panel i dalje radi
        # (taj endpoint INNER JOIN-a na devices)
        device_ids_to_keep = {
            row[0]
            for row in db.query(AuditLog.device_id)
            .filter(
                AuditLog.event_type == "VOTE_ACCEPTED",
                AuditLog.event_metadata["election_id"].astext == str(keep_election.id),
                AuditLog.device_id.isnot(None),
            )
            .distinct()
            .all()
        }

        if other_ids_str:
            deleted_logs = (
                db.query(AuditLog)
                .filter(AuditLog.event_metadata["election_id"].astext.in_(other_ids_str))
                .delete(synchronize_session=False)
            )
        else:
            deleted_logs = 0

        if other_ids:
            db.query(Election).filter(Election.id.in_(other_ids)).delete(synchronize_session=False)

        deleted_tokens = db.query(VoteToken).delete(synchronize_session=False)

        device_query = db.query(Device)
        if device_ids_to_keep:
            device_query = device_query.filter(Device.id.notin_(device_ids_to_keep))
        deleted_devices = device_query.delete(synchronize_session=False)

        db.commit()

        print("\nGotovo.")
        print(f"  - Obrisano izbora: {len(others)}")
        print(f"  - Obrisano audit log zapisa (vezanih za obrisane izbore): {deleted_logs}")
        print(f"  - Resetirano tokena: {deleted_tokens}")
        print(f"  - Obrisano uređaja (nekorištenih za zadržani izbor): {deleted_devices}")
        print(f"  - Uređaja zadržano (korišteno za \"{keep_election.name}\"): {len(device_ids_to_keep)}")
        print(f'\nBaza sad ima TOČNO JEDAN izbor: "{keep_election.name}" ({keep_vote_count} glasova).')
        print("Svih 129 službenih birališta i admin račun su netaknuti.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
