# Glasački terminal — E-Glasanje

React + Bootstrap sučelje glasačke kabine (FAZA 7). Prati tok iz poglavlja 12
projektne specifikacije: unos ključa → validacija → izbor kandidata → potvrda
→ glas zaprimljen.

## Pokretanje

```
npm install
copy .env.example .env
```

U `.env` upiši `VITE_DEVICE_KEY` — device API ključ terminala dobiven pri
registraciji uređaja (Faza 4/5, admin endpoint `POST /stations/{id}/devices`).

```
npm run dev
```

Backend (FastAPI) mora raditi na `http://127.0.0.1:8000` (ili adresi
postavljenoj u `VITE_API_BASE_URL`), s CORS-om dopuštenim za `localhost:5173`.

## Sigurnosne napomene (ne mijenjati bez razloga)

- Terminal nikad ne sprema ni prikazuje ništa osim onoga što backend vrati.
- `X-Device-Key` je tajna tog terminala — nikad se ne prikazuje na ekranu
  biraču, samo se šalje u headeru svakog API poziva.
- Nakon uspješnog/neuspješnog glasanja i nakon perioda neaktivnosti, terminal
  se sam vraća na početni ekran (vidi `IDLE_RESET_MS` i `SUCCESS_DISPLAY_MS`
  u `src/App.jsx`) — sljedeći birač ne smije naslijediti tuđu sesiju.
