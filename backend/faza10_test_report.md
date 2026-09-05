# FAZA 10 - Izvještaj sigurnosnog testiranja

Generirano: 2026-09-04 17:22 UTC

**Rezultat: SVI TESTOVI PROŠLI**

Prati FAZE_IMPLEMENTACIJE.md, poglavlje FAZA 10. Ovaj izvjestaj je izravan izlaz skripte `faza10_security_test.py` (nije rucno pisan) - pokrenut protiv zivog backend servera, s pravim HTTP pozivima.

## Prioritetni testovi (moraju proci)

### Test 1: Race condition na tokenu (RULE 05/06) - ✅ PROŠAO

- Poslano 20 ISTOVREMENIH zahtjeva (asyncio.gather) na isti token.
- Uspješno prihvaćeno (201): 1 (očekivano: točno 1)
- Odbijeno kao već iskorišten (409 TOKEN_ALREADY_USED): 19 (očekivano: 19)
- Neočekivani odgovori: 0
- Dokazuje da atomična `UPDATE ... WHERE status='AVAILABLE' RETURNING id` tranzicija (poglavlje 11) stvarno sprječava dvostruko glasanje pod konkurencijom, ne samo u teoriji.

### Test 2: Nepostojeći token - ✅ PROŠAO

- POST /voting/cast s nepostojećim tokenom -> HTTP 404, error_code=INVALID_TOKEN
- Očekivano: HTTP 404, error_code=INVALID_TOKEN.

### Test 3: Replay / već iskorišten token - ✅ PROŠAO

- Prvi pokušaj (svjež token) -> HTTP 201 (očekivano: 201)
- Drugi pokušaj (ISTI token, ispravnog formata) -> HTTP 409, error_code=TOKEN_ALREADY_USED (očekivano: 409 TOKEN_ALREADY_USED)

### Test 4: Neautoriziran pristup admin API-ju - ✅ PROŠAO

- /elections (bez tokena) -> HTTP 401 (očekivano: 401)
- /elections (neispravan token) -> HTTP 401 (očekivano: 401)
- /stations (bez tokena) -> HTTP 401 (očekivano: 401)
- /stations (neispravan token) -> HTTP 401 (očekivano: 401)
- /audit-logs (bez tokena) -> HTTP 401 (očekivano: 401)
- /audit-logs (neispravan token) -> HTTP 401 (očekivano: 401)

## Sekundarno - mitigirano dizajnom (nije ovdje automatski testirano)

Prema FAZE_IMPLEMENTACIJE.md, ovi rizici su svjesno mitigirani arhitekturnom odlukom umjesto rucnim iscrpnim testiranjem, radi ustede vremena u 7-dnevnom roku:

- **SQL injection** - mitigirano koristenjem SQLAlchemy ORM-a sa parametriziranim upitima; nigdje u kodu se ne radi rucna konkatenacija SQL stringova (provjereno pregledom svih routera - app/*/router.py koriste iskljucivo `db.query(...)`/ORM izraze).
- **XSS** - mitigirano time sto React (frontend-admin, frontend-terminal) po defaultu escapea sav sadrzaj koji renderira; `dangerouslySetInnerHTML` se nigdje u projektu ne koristi (provjereno pretragom koda).
- **CSRF** - mitigirano time sto admin autentikacija koristi bearer JWT u Authorization headeru, ne kolacice (poglavlje 34.4) - CSRF je relevantan uglavnom kod cookie-based sesija gdje browser sam automatski salje kolacic; ovdje token mora rucno postaviti frontend JS kod, sto stranica treceg izvora ne moze ucini bez pristupa localStorage/memoriji nase aplikacije.

## Napomena o testnim podacima

Ova skripta kreira privremeni testni izbor radi provedbe testova. Prije predaje/demo-a, pokreni `reset_test_data.py` da obrises sve testne izbore/glasove/uredjaje (ukljucujuci i ove) i vratis bazu na cisto stanje sa svih 129 sluzbenih biralista.
