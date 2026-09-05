"""
FAZA 10 - Ciljano sigurnosno testiranje (prilagodjeno 7-dnevnom roku).

Prati FAZE_IMPLEMENTACIJE.md, poglavlje FAZA 10. Automatski provjerava
cetiri PRIORITETNA slucaja iz specifikacije:

  1. Race condition na tokenu (RULE 05/06) - N istovremenih zahtjeva na
     ISTI token, mora proci TOCNO jedan.
  2. Invalid token - nepostojeci token se odbija (404 INVALID_TOKEN).
  3. Replay / already-used token - vec iskoristen token se odbija (409
     TOKEN_ALREADY_USED), cak i uz ispravan format.
  4. Neautoriziran pristup admin API-ju - admin endpointi bez/s
     neispravnim JWT-om vracaju 401.

Skripta sama kreira privremeni testni izbor ("FAZA10 Sigurnosni test ...")
s 2 kandidata i JEDNIM privremenim uredjajem na prvom dostupnom biralistu,
provede sva 4 testa, ispise rezultate u terminal I napise strukturirani
Markdown izvjestaj (faza10_test_report.md) pored ove skripte - taj
izvjestaj je deliverable trazen u FAZE_IMPLEMENTACIJE.md.

Testni izbor se na kraju zatvara, a sam testni podaci (izbor, kandidati,
uredjaj, tokeni, glasovi) su namjerno odvojeni od "pravih" demo podataka -
ako zelis potpuno cist prompt za predaju, reset_test_data.py na kraju
obrise SVE izbore/glasove/uredjaje (pa i ove testne).

Pokreni iz IVAN_zav/backend foldera:
    .\\venv\\Scripts\\python.exe faza10_security_test.py
"""

import asyncio
import getpass
import sys
from datetime import datetime, timezone

import httpx

BASE_URL = "http://127.0.0.1:8000"
RACE_CONCURRENCY = 20  # broj istovremenih zahtjeva na isti token


class Reporter:
    """Skuplja rezultate testova radi ispisa u terminal i u Markdown izvjestaj."""

    def __init__(self):
        self.sections = []  # [(title, passed, detail_lines)]

    def add(self, title: str, passed: bool, detail_lines: list[str]):
        self.sections.append((title, passed, detail_lines))
        status = "PROŠAO" if passed else "PAO"
        print(f"\n{'=' * 70}\n[{status}] {title}\n{'=' * 70}")
        for line in detail_lines:
            print(f"  {line}")

    def all_passed(self) -> bool:
        return all(passed for _, passed, _ in self.sections)

    def to_markdown(self) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        overall = "SVI TESTOVI PROŠLI" if self.all_passed() else "NEKI TESTOVI NISU PROŠLI - vidi detalje"
        lines = [
            "# FAZA 10 - Izvještaj sigurnosnog testiranja",
            "",
            f"Generirano: {now}",
            "",
            f"**Rezultat: {overall}**",
            "",
            "Prati FAZE_IMPLEMENTACIJE.md, poglavlje FAZA 10. Ovaj izvjestaj je "
            "izravan izlaz skripte `faza10_security_test.py` (nije rucno pisan) - "
            "pokrenut protiv zivog backend servera, s pravim HTTP pozivima.",
            "",
            "## Prioritetni testovi (moraju proci)",
            "",
        ]
        for title, passed, detail_lines in self.sections:
            status = "✅ PROŠAO" if passed else "❌ PAO"
            lines.append(f"### {title} - {status}")
            lines.append("")
            for line in detail_lines:
                lines.append(f"- {line}")
            lines.append("")

        lines.extend(
            [
                "## Sekundarno - mitigirano dizajnom (nije ovdje automatski testirano)",
                "",
                "Prema FAZE_IMPLEMENTACIJE.md, ovi rizici su svjesno mitigirani "
                "arhitekturnom odlukom umjesto rucnim iscrpnim testiranjem, radi "
                "ustede vremena u 7-dnevnom roku:",
                "",
                "- **SQL injection** - mitigirano koristenjem SQLAlchemy ORM-a sa "
                "parametriziranim upitima; nigdje u kodu se ne radi rucna "
                "konkatenacija SQL stringova (provjereno pregledom svih routera - "
                "app/*/router.py koriste iskljucivo `db.query(...)`/ORM izraze).",
                "- **XSS** - mitigirano time sto React (frontend-admin, "
                "frontend-terminal) po defaultu escapea sav sadrzaj koji renderira; "
                "`dangerouslySetInnerHTML` se nigdje u projektu ne koristi "
                "(provjereno pretragom koda).",
                "- **CSRF** - mitigirano time sto admin autentikacija koristi "
                "bearer JWT u Authorization headeru, ne kolacice (poglavlje 34.4) - "
                "CSRF je relevantan uglavnom kod cookie-based sesija gdje browser "
                "sam automatski salje kolacic; ovdje token mora rucno postaviti "
                "frontend JS kod, sto stranica treceg izvora ne moze ucini bez "
                "pristupa localStorage/memoriji nase aplikacije.",
                "",
                "## Napomena o testnim podacima",
                "",
                "Ova skripta kreira privremeni testni izbor radi provedbe testova. "
                "Prije predaje/demo-a, pokreni `reset_test_data.py` da obrises sve "
                "testne izbore/glasove/uredjaje (ukljucujuci i ove) i vratis bazu "
                "na cisto stanje sa svih 129 sluzbenih biralista.",
                "",
            ]
        )
        return "\n".join(lines)


def fail(reporter: Reporter, msg: str):
    print(f"\nFATALNA GREŠKA: {msg}")
    print("Testiranje prekinuto.")
    report_path = write_report(reporter)
    print(f"\nDjelomičan izvještaj spremljen: {report_path}")
    sys.exit(1)


def write_report(reporter: Reporter) -> str:
    from pathlib import Path

    path = Path(__file__).resolve().parent / "faza10_test_report.md"
    path.write_text(reporter.to_markdown(), encoding="utf-8")
    return str(path)


async def main():
    print("=== FAZA 10 - Sigurnosno testiranje ===\n")
    username = input("Admin korisničko ime: ").strip()
    password = getpass.getpass("Admin lozinka: ")

    reporter = Reporter()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=15.0) as client:
        # --- Prijava --------------------------------------------------------
        resp = await client.post("/auth/login", json={"username": username, "password": password})
        if resp.status_code != 200:
            fail(reporter, f"Prijava nije uspjela ({resp.status_code}): {resp.text}")
        admin_token = resp.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("Prijava uspješna.\n")

        # --- Priprema: testni izbor, kandidati, biralište, uređaj -----------
        stations_resp = await client.get("/stations", headers=admin_headers)
        stations = stations_resp.json()
        if not stations:
            fail(reporter, "Nema registriranih biračkih mjesta - ne mogu pripremiti testno okruženje.")
        station = stations[0]
        print(f"Koristim biralište za test: {station['code']} - {station['name']}")

        election_name = f"FAZA10 Sigurnosni test {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        create_resp = await client.post("/elections", json={"name": election_name}, headers=admin_headers)
        if create_resp.status_code != 201:
            fail(reporter, f"Kreiranje testnog izbora nije uspjelo: {create_resp.text}")
        election = create_resp.json()["election"] if "election" in create_resp.json() else create_resp.json()
        election_id = election["id"]
        print(f"Testni izbor kreiran: {election_name} ({election_id})")

        for cand_name in ["Test Kandidat A", "Test Kandidat B"]:
            c_resp = await client.post(
                f"/elections/{election_id}/candidates", json={"name": cand_name}, headers=admin_headers
            )
            if c_resp.status_code != 201:
                fail(reporter, f"Dodavanje kandidata nije uspjelo: {c_resp.text}")
        candidates_resp = await client.get(f"/elections/{election_id}/candidates", headers=admin_headers)
        candidates = candidates_resp.json()
        candidate_id = candidates[0]["id"]

        open_resp = await client.post(f"/elections/{election_id}/open", headers=admin_headers)
        if open_resp.status_code != 200:
            fail(reporter, f"Otvaranje testnog izbora nije uspjelo: {open_resp.text}")
        print("Testni izbor otvoren.")

        device_code = f"FAZA10-TEST-{datetime.now().strftime('%H%M%S')}"
        device_resp = await client.post(
            f"/stations/{station['id']}/devices", json={"device_code": device_code}, headers=admin_headers
        )
        if device_resp.status_code != 201:
            fail(reporter, f"Registracija testnog uređaja nije uspjela: {device_resp.text}")
        device_key = device_resp.json()["api_key"]
        device_headers = {"X-Device-Key": device_key}
        print(f"Testni uređaj registriran: {device_code}\n")

        # =====================================================================
        # TEST 1 - Race condition na tokenu (NAJVAŽNIJI test)
        # =====================================================================
        tok_resp = await client.post(
            f"/stations/{station['id']}/tokens/generate",
            json={"count": 1, "force": True},
            headers=admin_headers,
        )
        if tok_resp.status_code != 201:
            fail(reporter, f"Generiranje tokena za race-condition test nije uspjelo: {tok_resp.text}")
        race_token = tok_resp.json()["tokens"][0]

        async def cast_attempt():
            try:
                r = await client.post(
                    "/voting/cast",
                    json={"token": race_token, "candidate_id": candidate_id},
                    headers=device_headers,
                )
                return r.status_code, r.json().get("error_code") if r.status_code >= 400 else None
            except Exception as exc:  # noqa: BLE001
                return None, str(exc)

        results = await asyncio.gather(*[cast_attempt() for _ in range(RACE_CONCURRENCY)])
        successes = [r for r in results if r[0] == 201]
        rejections = [r for r in results if r[0] == 409]
        other = [r for r in results if r not in successes and r not in rejections]

        race_pass = len(successes) == 1 and len(rejections) == RACE_CONCURRENCY - 1
        reporter.add(
            "Test 1: Race condition na tokenu (RULE 05/06)",
            race_pass,
            [
                f"Poslano {RACE_CONCURRENCY} ISTOVREMENIH zahtjeva (asyncio.gather) na isti token.",
                f"Uspješno prihvaćeno (201): {len(successes)} (očekivano: točno 1)",
                f"Odbijeno kao već iskorišten (409 TOKEN_ALREADY_USED): {len(rejections)} "
                f"(očekivano: {RACE_CONCURRENCY - 1})",
                f"Neočekivani odgovori: {len(other)}" + (f" -> {other}" if other else ""),
                "Dokazuje da atomična `UPDATE ... WHERE status='AVAILABLE' RETURNING id` "
                "tranzicija (poglavlje 11) stvarno sprječava dvostruko glasanje pod "
                "konkurencijom, ne samo u teoriji.",
            ],
        )

        # =====================================================================
        # TEST 2 - Invalid token
        # =====================================================================
        fake_token = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # sintaktički moguć, ne postoji u bazi
        r2 = await client.post(
            "/voting/cast",
            json={"token": fake_token, "candidate_id": candidate_id},
            headers=device_headers,
        )
        test2_pass = r2.status_code == 404 and r2.json().get("error_code") == "INVALID_TOKEN"
        reporter.add(
            "Test 2: Nepostojeći token",
            test2_pass,
            [
                f"POST /voting/cast s nepostojećim tokenom -> HTTP {r2.status_code}, "
                f"error_code={r2.json().get('error_code')}",
                "Očekivano: HTTP 404, error_code=INVALID_TOKEN.",
            ],
        )

        # =====================================================================
        # TEST 3 - Replay / already-used token (izvan race-condition testa,
        # čist sekvencijalni slučaj - jedan uspješan cast pa ponovni pokušaj)
        # =====================================================================
        tok2_resp = await client.post(
            f"/stations/{station['id']}/tokens/generate",
            json={"count": 1, "force": True},
            headers=admin_headers,
        )
        replay_token = tok2_resp.json()["tokens"][0]
        first_cast = await client.post(
            "/voting/cast",
            json={"token": replay_token, "candidate_id": candidate_id},
            headers=device_headers,
        )
        second_cast = await client.post(
            "/voting/cast",
            json={"token": replay_token, "candidate_id": candidate_id},
            headers=device_headers,
        )
        test3_pass = (
            first_cast.status_code == 201
            and second_cast.status_code == 409
            and second_cast.json().get("error_code") == "TOKEN_ALREADY_USED"
        )
        reporter.add(
            "Test 3: Replay / već iskorišten token",
            test3_pass,
            [
                f"Prvi pokušaj (svjež token) -> HTTP {first_cast.status_code} (očekivano: 201)",
                f"Drugi pokušaj (ISTI token, ispravnog formata) -> HTTP {second_cast.status_code}, "
                f"error_code={second_cast.json().get('error_code')} "
                f"(očekivano: 409 TOKEN_ALREADY_USED)",
            ],
        )

        # =====================================================================
        # TEST 4 - Neautoriziran pristup admin API-ju
        # =====================================================================
        admin_endpoints = [
            ("GET", "/elections"),
            ("GET", "/stations"),
            ("GET", "/audit-logs"),
        ]
        unauth_results = []
        for method, path in admin_endpoints:
            r_none = await client.request(method, path)  # bez Authorization headera
            r_garbage = await client.request(method, path, headers={"Authorization": "Bearer ovo-nije-jwt"})
            unauth_results.append((path, "bez tokena", r_none.status_code))
            unauth_results.append((path, "neispravan token", r_garbage.status_code))

        test4_pass = all(code == 401 for _, _, code in unauth_results)
        reporter.add(
            "Test 4: Neautoriziran pristup admin API-ju",
            test4_pass,
            [f"{path} ({variant}) -> HTTP {code} (očekivano: 401)" for path, variant, code in unauth_results],
        )

        # --- Čišćenje: zatvori testni izbor ----------------------------------
        await client.post(f"/elections/{election_id}/close", headers=admin_headers)
        print(f"\nTestni izbor zatvoren ({election_name}).")

    # --- Sažetak i izvještaj -------------------------------------------------
    report_path = write_report(reporter)
    print(f"\n{'=' * 70}")
    print("SVI TESTOVI PROŠLI" if reporter.all_passed() else "NEKI TESTOVI NISU PROŠLI - vidi detalje iznad")
    print(f"{'=' * 70}")
    print(f"\nIzvještaj spremljen: {report_path}")
    print(
        "\nNapomena: ovaj testni izbor ostaje u bazi (zatvoren) dok ne pokreneš "
        "reset_test_data.py prije predaje."
    )


if __name__ == "__main__":
    asyncio.run(main())
