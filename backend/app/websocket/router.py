"""
FAZA 8 - /ws/admin endpoint za Admin Dashboard (poglavlje 14).
FAZA 9 (dopuna) - /ws/status endpoint za glasacke terminale.

Autentikacija (34.3): JWT se salje kao PRVA poruka NAKON sto se veza vec
uspostavi - NIKAD u URL-u/query stringu (query stringovi zavrsavaju u
access/proxy logovima, sto bi bilo curenje admin tokena).

WebSocket NIKAD ne odlucuje o glasanju (poglavlje 15) - ovaj router samo
prima vec gotove evente od broadcaster.py i prosljedjuje ih spojenim
klijentima.

/ws/status NEMA autentikaciju - namjerno, jer poruke koje na njemu smiju
zavrsiti (vidi broadcast_public_event u broadcaster.py) nikad ne nose
nista osjetljivo (RULE 08/09). Terminal ga koristi ISKLJUCIVO kao "nesto
se promijenilo, provjeri ponovno" signal - i dalje mora sam dohvatiti
stvarne podatke preko REST-a (GET /voting/current-election), WS mu nista
ne "govori" izravno.
"""

import asyncio
import logging

import jwt as pyjwt
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.auth.security import decode_access_token
from app.websocket.manager import manager

logger = logging.getLogger("evoting.websocket")
router = APIRouter(tags=["websocket"])

AUTH_TIMEOUT_SECONDS = 10
# WS close kod iz privatnog raspona (4000-4999) - "aplikacijska" greska,
# da se razlikuje od standardnih protokolnih WS kodova
WS_CLOSE_UNAUTHORIZED = 4401


@router.websocket("/ws/admin")
async def admin_websocket(websocket: WebSocket) -> None:
    await websocket.accept()

    try:
        first_message = await asyncio.wait_for(websocket.receive_json(), timeout=AUTH_TIMEOUT_SECONDS)
    except (TimeoutError, WebSocketDisconnect, ValueError):
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED, reason="Auth timeout")
        return

    token = first_message.get("token") if isinstance(first_message, dict) else None
    if not token:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED, reason="Missing token")
        return

    try:
        decode_access_token(token)
    except pyjwt.PyJWTError:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED, reason="Invalid token")
        return

    await manager.connect_admin(websocket)
    logger.info("ADMIN_WS_CONNECTED")
    await websocket.send_json({"type": "connected"})

    try:
        while True:
            # Ne ocekujemo puno poruka od admin dashboarda - ova petlja
            # postoji da (a) detektiramo prekid veze (WebSocketDisconnect)
            # i (b) omogucimo jednostavan heartbeat (klijent salje "ping",
            # mi odgovaramo "pong" - dashboard time zna da je veza ziva).
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_admin(websocket)
        logger.info("ADMIN_WS_DISCONNECTED")


@router.websocket("/ws/status")
async def status_websocket(websocket: WebSocket) -> None:
    # Bez auth handshakea (vidi docstring modula) - odmah spajamo.
    await websocket.accept()
    await manager.connect_status(websocket)
    logger.info("STATUS_WS_CONNECTED")
    await websocket.send_json({"type": "connected"})

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_status(websocket)
        logger.info("STATUS_WS_DISCONNECTED")
