"""
FAZA 9 zavrsni korak - "veliki" pokazni izbor za predaju profesoru.

Simulira glasanje na SVIH 129 sluzbenih biralista, svako s nasumicnim brojem
glasova izmedju 1 i 20, blago neravnomjerno rasporedjenih po kandidatima (da
grafovi na Tally ekranu izgledaju realisticno, ne kao savrsen remi) - koji
kandidat "vodi" je nasumicno drugaciji svaki put kad se skripta pokrene
(vidi random.shuffle(weights) nize), ne uvijek isti.

Ovo je velika simulacija (~129 biralista, potencijalno preko 1000 glasova
ukupno) - potraje nekoliko minuta, to je ocekivano i normalno.

Za svako biraliste skripta:
  1. registrira NOVI uredjaj (da ne mora nagadjati/imati vec postojeci API kljuc)
  2. generira svjez pool tokena TOCNO velicine planiranog broja glasova (force=True)
  3. odmah "odglasa" svaki token preko PRAVOG /voting/cast API poziva (isto sto
     radi i glasacki terminal) - prava enkripcija, integrity_hash lanac, audit
     log, WebSocket broadcast - ništa se ne upisuje izravno u bazu

Namjerno postoji kratka pauza izmedju glasova - da se na admin "Nadzor uzivo"
ekranu (otvorenom u pregledniku dok skripta radi) vidi kako brojevi rastu
UZIVO, ne da se sve pojavi odjednom.

Ne zatvara izbor - to admin radi rucno kroz konzolu kad je gotovo (dio
zajednickog testa svih znacajki).

Treba postojeci OTVOREN izbor s vec dodanim kandidatima (poglavlje "Izbori i
kandidati" u admin konzoli).

Pokreni iz IVAN_zav/backend foldera:
    .\\venv\\Scripts\\python.exe simulate_election.py
"""

import getpass
import json
import random
import time
import urllib.error
import urllib.request
import uuid

BASE_URL = "http://127.0.0.1:8000"

MIN_VOTES_PER_STATION = 1
MAX_VOTES_PER_STATION = 20


def api_request(method, path, body=None, admin_token=None, device_key=None):
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if admin_token:
        req.add_header("Authorization", f"Bearer {admin_token}")
    if device_key:
        req.add_header("X-Device-Key", device_key)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {path} -> HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ne mogu se spojiti na {BASE_URL} - je li backend pokrenut? ({exc})") from exc


def main():
    print("=== Simulacija veceg pokaznog izbora ===\n")
    username = input("Admin korisnicko ime: ").strip()
    password = getpass.getpass("Admin lozinka: ")

    login = api_request("POST", "/auth/login", {"username": username, "password": password})
    admin_token = login["access_token"]
    print("Prijava uspjesna.\n")

    elections = api_request("GET", "/elections", admin_token=admin_token)
    open_elections = [e for e in elections if e["status"] == "OPEN"]
    if not open_elections:
        print("Nema trenutno OTVORENOG izbora. Otvori izbor u admin konzoli pa pokreni skriptu ponovno.")
        return
    if len(open_elections) > 1:
        print("Vise otvorenih izbora, odaberi jedan:")
        for i, e in enumerate(open_elections):
            print(f"  {i + 1}. {e['name']}")
        choice = int(input("Broj: ").strip()) - 1
        election = open_elections[choice]
    else:
        election = open_elections[0]
    print(f"Izbor: \"{election['name']}\"\n")

    candidates = api_request("GET", f"/elections/{election['id']}/candidates", admin_token=admin_token)
    if not candidates:
        print("Izbor nema dodanih kandidata. Dodaj kandidate prije pokretanja skripte.")
        return
    candidates.sort(key=lambda c: c["display_order"])
    print("Kandidati:", ", ".join(c["name"] for c in candidates))

    # Blago neravnomjerni tezinski faktori - realisticnija razdioba na Tally
    # grafovima nego savrseno ravnomjeran remi. NASUMICNO promijesani preko
    # random.shuffle SVAKI put kad se skripta pokrene, umjesto da se uvijek
    # dodijele redoslijedom kandidata (sto bi znacilo da prvi dodani kandidat
    # UVIJEK "pobjedjuje") - koji kandidat vodi je tako drugaciji iz
    # pokretanja u pokretanje.
    base_weights = [0.38, 0.28, 0.20, 0.14]
    weights = [base_weights[i % len(base_weights)] for i in range(len(candidates))]
    random.shuffle(weights)

    stations = api_request("GET", "/stations", admin_token=admin_token)
    stations_by_code = {s["code"]: s for s in stations}

    # SVIH sluzbenih birališta (obicno 129), ne samo podskup - svaki put
    # kad se skripta pokrene.
    plan = [(code, random.randint(MIN_VOTES_PER_STATION, MAX_VOTES_PER_STATION)) for code in stations_by_code]

    total_planned = sum(count for _, count in plan)
    print(f"\nPlan: {len(plan)} birališta, ukupno {total_planned} glasova.")
    print("Ovo ce potrajati nekoliko minuta (namjerna pauza izmedju glasova, vidi docstring).\n")
    confirm = input('Upisi "DA" za pokretanje (bilo sto drugo odustaje): ')
    if confirm.strip() != "DA":
        print("Odustao/la si - ništa nije poslano.")
        return

    print("\nPokrecem - prati 'Nadzor uzivo' u admin konzoli u pregledniku...\n")

    grand_total = 0
    candidate_totals = {c["id"]: 0 for c in candidates}

    for code, count in plan:
        station = stations_by_code[code]
        device_code = f"{code}-DEMO-{uuid.uuid4().hex[:6].upper()}"

        try:
            device_resp = api_request(
                "POST",
                f"/stations/{station['id']}/devices",
                {"device_code": device_code},
                admin_token=admin_token,
            )
            api_key = device_resp["api_key"]

            tokens_resp = api_request(
                "POST",
                f"/stations/{station['id']}/tokens/generate",
                {"count": count, "force": True},
                admin_token=admin_token,
            )
            tokens = tokens_resp["tokens"]
        except RuntimeError as exc:
            print(f"[{code}] GRESKA pri pripremi - preskačem biraliste: {exc}")
            continue

        cast_ok = 0
        for tok in tokens:
            candidate = random.choices(candidates, weights=weights, k=1)[0]
            try:
                api_request(
                    "POST",
                    "/voting/cast",
                    {"token": tok, "candidate_id": candidate["id"]},
                    device_key=api_key,
                )
                cast_ok += 1
                candidate_totals[candidate["id"]] += 1
                grand_total += 1
            except RuntimeError as exc:
                print(f"[{code}] GRESKA pri glasanju - preskačem taj glas: {exc}")
            time.sleep(random.uniform(0.08, 0.25))

        print(f"[{code}] {cast_ok}/{count} glasova uspjesno poslano.")

    print(f"\nGotovo. Ukupno poslano {grand_total} glasova na {len(plan)} birališta.")
    print("Razdioba po kandidatu:")
    for c in candidates:
        print(f"  {c['name']}: {candidate_totals[c['id']]}")
    print('\nSlijedi: zatvori izbor u admin konzoli ("Zatvori izbor"), pa idi na Nadzor -> Tally za rezultate.')


if __name__ == "__main__":
    main()
