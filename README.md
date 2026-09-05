# E-Glasanje — pokretanje sustava

Za pregled projekta trebaju raditi dva servisa istovremeno, svaki u svom
terminalu. Redoslijed je bitan — prvo Terminal 1, tek onda Terminal 2.

## Terminal 1 — Backend

Otvori terminal, pa redom:

```
cd backend
.\venv\Scripts\activate
```

Provjeri ispis: na početku retka u terminalu sad piše `(venv)` prije puta
do foldera. Ako ne piše, nešto nije aktivirano — ne nastavljaj dalje dok
ovo ne piše.

```
uvicorn app.main:app --reload
```

Provjeri ispis: zadnje dvije linije trebaju biti otprilike

```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

Ako umjesto toga piše nešto s "Error" ili "Traceback" — zastani, ne
nastavljaj na Terminal 2, javi mi točan ispis.

Ovaj terminal ostaje otvoren i uključen cijelo vrijeme dok se sustav
koristi — ne zatvaraj ga.

## Terminal 2 — Admin konzola

Novi, drugi terminal (Terminal 1 ostaje otvoren u pozadini):

```
cd frontend-admin
npm run dev
```

Provjeri ispis: treba se pojaviti nešto poput

```
  ➜  Local:   http://localhost:5174/
```

(broj porta može biti i drugačiji, npr. 5173 — nije problem, samo koristi
adresu koju terminal ispiše).

Ovaj terminal isto ostaje otvoren cijelo vrijeme.

## Otvori sučelje

U browseru otvori adresu koju je ispisao Terminal 2 (npr.
`http://localhost:5174`). Prijavi se s admin korisničkim imenom i
lozinkom.

## Korištenje sustava

### Kako provesti cijeli izbor od nule

1. **Tab "Izbori i kandidati"** → dolje "Novi izbor" → upiši naziv →
   **Kreiraj izbor**. Zatim dodaj kandidate (ime pa Dodaj, za svakog
   kandidata posebno).
2. Na tom istom izboru klikni **Otvori izbor**. Odmah nakon toga se
   prikaže **privatni ključ** — to je JEDINI put kad se prikazuje, sustav
   ga nigdje ne sprema. Kopiraj ga i spremi negdje sigurno (npr. u .txt
   datoteku) — bez njega se glasovi kasnije ne mogu prebrojati.
3. **Tab "Biračka mjesta"** — svih 129 službenih birališta već postoji,
   ne treba ništa dodavati.
4. **Tab "Uređaji i tokeni"** → odaberi biralište → **Dodaj** (registrira
   uređaj, prikaže se API ključ uređaja — isto samo JEDNOM, treba ga za
   Terminal 3 niže) → **Generiraj** (broj tokena = broj glasova koje želiš
   simulirati). Tokeni se mogu preuzeti gumbom "Preuzmi sve kao .txt".
   (Postoje i brzi gumbi "Registriraj uređaje na sva birališta bez
   uređaja" / "Generiraj tokene za sva birališta" ako želiš sve odjednom.)
5. **Glasanje** — pokreni Terminal 3 (uputa niže), u `.env` upiši
   `VITE_DEVICE_KEY` = API ključ uređaja iz koraka 4, otvori
   `http://localhost:5173`, unesi jedan od tokena iz koraka 4, odaberi
   kandidata, potvrdi.
6. Kad je dosta glasova ubačeno, natrag u **"Izbori i kandidati"** →
   **Zatvori izbor**.
7. **Tab "Nadzor"** → odaberi taj izbor iz padajućeg izbornika → dolje
   kartica **"Brojanje glasova (Tally)"** → zalijepi privatni ključ iz
   koraka 2 → **Prebroji glasove**.

### Dijelovi taba "Nadzor"

- **Padajući izbornik "Izbor"** (na vrhu) — bira se koji se izbor gleda;
  pored njega status: `NIJE OTVOREN` / `OTVOREN` / `ZATVOREN`.
- **"Glasovi po biralištu"** (rasklopivo, klik na naslov) — broj glasova
  po biralištu, uživo preko WebSocketa dok se glasa.
- **"Glasovi po uređaju"** — isto, ali po pojedinom uređaju, ne samo po
  biralištu (korisno ako jedno biralište ima više uređaja/kabina).
- **"Sigurnosni i sistemski događaji"** — audit log: prijave admina,
  otvaranje/zatvaranje izbora, pokušaji s nevažećim ili već iskorištenim
  tokenom (istaknuto žutom bojom), i slično.
- Dok je izbor **OTVOREN**: kartica **"Izlaznost uživo"** — samo ukupni
  brojevi i postotak izlaznosti po regiji/županiji, namjerno BEZ podjele
  po kandidatu (ta podjela se ne može ni izračunati dok je izbor otvoren
  — glasovi su enkriptirani do zatvaranja).
- Dok je izbor **ZATVOREN**: kartica **"Brojanje glasova (Tally)"** —
  nakon unosa ključa i klika na "Prebroji glasove", prikazuju se puni
  rezultati: graf po kandidatu, grafovi po NUTS2 regiji i županiji
  (stupci obojeni po kandidatu, os s brojevima sa strane), i popis po
  biralištu.

## Terminal 3 — Glasački terminal (opcionalno)

Samo ako želiš vidjeti i sučelje glasačke kabine / stvarno glasati, ne
treba za pregled već izbrojanih rezultata u admin konzoli.

Prvi put treba upisati ključ uređaja: otvori
`frontend-terminal\.env` (kopiju `.env.example` ako `.env` još ne
postoji) i u `VITE_DEVICE_KEY=` zalijepi API ključ uređaja (dobiven u
koraku 4 gore, "Uređaji i tokeni"). Spremi datoteku.

```
cd frontend-terminal
npm run dev
```

Otvara se na adresi koju terminal ispiše (npr. `http://localhost:5173`).

## Gašenje

U svakom terminalu koji je ostao otvoren: `Ctrl+C`.
