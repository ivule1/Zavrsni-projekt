"""
WebSocket broadcasting (FAZA 8, prosireno u Fazi 9).

Prije Faze 8 ovo je bio placeholder koji je samo logirao namjeru - sad
stvarno salje spojenim klijentima preko ConnectionManagera.

Poruke moraju biti minimalne (poglavlje 26) - NIKAD token, candidate_id
niti sadrzaj glasa (RULE 09). Poziva se TEK nakon uspjesnog DB commita
(poglavlje 15) - vidi app/voting/router.py i app/elections/router.py.

Dvije funkcije, dva razlicita "audiencea" (vidi app/websocket/manager.py):
- broadcast_event() - SAMO admin dashboardu (npr. vote_count)
- broadcast_public_event() - admin dashboardu I glasackim terminalima,
  koristi se iskljucivo za evente koji ne nose NIKAKAV osjetljiv sadrzaj
  (npr. election_changed - terminal ga koristi samo kao signal da
  ponovno dohvati trenutni izbor preko REST-a, poglavlje 15 princip)
"""

import logging

from app.websocket.manager import manager

logger = logging.getLogger("evoting.websocket")


def broadcast_event(event: dict) -> None:
    logger.info("WS_EVENT %s", event)
    manager.broadcast_admin(event)


def broadcast_public_event(event: dict) -> None:
    logger.info("WS_EVENT_PUBLIC %s", event)
    manager.broadcast_all(event)
