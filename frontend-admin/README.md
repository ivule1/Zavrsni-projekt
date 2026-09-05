# Admin nadzor — E-Glasanje

React + Bootstrap admin dashboard (FAZA 9). Prijava, popis izbora, uživo
broj glasova po biralištu (preko `/ws/admin`, Faza 8), i Tally ekran za
dešifriranje glasova nakon zatvaranja izbora (poglavlje 34.1).

## Pokretanje

```
npm install
copy .env.example .env
npm run dev
```

Backend (FastAPI) mora raditi na `http://127.0.0.1:8000` (ili adresi
postavljenoj u `.env`), s CORS-om dopuštenim za ovaj dev server (provjeri
`VITE_API_BASE_URL`/`VITE_WS_BASE_URL` odgovaraju adresi backenda i port se
ne poklapa s terminalom iz Faze 7 — Vite će sam odabrati sljedeći slobodni
port, npr. `5174`, ako je `5173` zauzet terminalom).

## Sigurnosne napomene

- Admin JWT se drži samo u `sessionStorage` (preživi refresh stranice, ali
  nestaje kad se kartica zatvori) — nikad u `localStorage`.
- Privatni ključ izbora (za Tally) se unosi ručno pri svakom brojanju i
  **nikad se ne sprema** — ni u state nakon uspješnog zahtjeva, ni igdje
  lokalno (vidi `TallyPanel.jsx`).
- Dashboard prikazuje samo agregirane brojeve (glasovi po biralištu,
  ukupno) — nikad sadržaj pojedinačnog glasa niti bilo što vezano za
  identitet birača (poglavlje 16).
