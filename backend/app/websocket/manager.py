"""
FAZA 8 - pravi WebSocket connection manager (zamjena za placeholder iz Faze 6).
FAZA 9 (dopuna) - prosireno na DVA odvojena "audiencea":

- admin_connections - /ws/admin, autenticirano JWT-om (poglavlje 14 - WS je
  prvenstveno za komunikaciju FastAPI <-> Admin Dashboard). Prima SVE
  evente (vote_count I election_changed).
- status_connections - /ws/status, namjerno BEZ autentikacije jer poruke na
  tom kanalu ne smiju nikad nositi nista osjetljivo (RULE 08/09) - koristi
  ga iskljucivo glasacki terminal, kao "nesto se promijenilo, provjeri
  ponovno" signal (npr. izbor je otvoren/zatvoren). Terminal NE prima
  vote_count evente - njemu ti podaci nisu ni potrebni, a nema smisla
  slati mu ih.

Drzimo ih odvojeno (a ne jednu zajednicku listu) da ostane ocito i lako
provjerljivo koji audience dobiva koji tip poruke - admin dashboard uvijek
sve, terminal samo ono sto mu je stvarno potrebno.

Vazna tehnicka odluka: `/voting/cast` (poglavlje 15 - DB commit MORA biti
prije WS eventa) je namjerno SINKRONA FastAPI ruta - FastAPI takve rute
pokrece u zasebnom threadpool threadu, ne na glavnom asyncio event loopu.
Slanje preko WebSocketa je async operacija koja mora ici na event loop.
`broadcast_admin()`/`broadcast_all()` zato premoscuju thread -> event loop
preko `asyncio.run_coroutine_threadsafe`, sto je standardan i siguran nacin
za ovo (dokumentirano ponasanje asyncio modula), umjesto da mijenjamo vec
testirani voting/router.py u async.
"""

import asyncio
import logging

from fastapi import WebSocket

logger = logging.getLogger("evoting.websocket")


class ConnectionManager:
    def __init__(self) -> None:
        self.admin_connections: list[WebSocket] = []
        self.status_connections: list[WebSocket] = []
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Poziva se JEDNOM, pri pokretanju aplikacije (main.py lifespan) -
        cuva referencu na glavni event loop da bismo mogli emitirati WS
        evente iz sinkronih ruta."""
        self._loop = loop

    async def connect_admin(self, websocket: WebSocket) -> None:
        self.admin_connections.append(websocket)

    def disconnect_admin(self, websocket: WebSocket) -> None:
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)

    async def connect_status(self, websocket: WebSocket) -> None:
        self.status_connections.append(websocket)

    def disconnect_status(self, websocket: WebSocket) -> None:
        if websocket in self.status_connections:
            self.status_connections.remove(websocket)

    async def _send_to(self, connections: list[WebSocket], message: dict) -> None:
        # kopija liste - ako se neka veza ugasi tijekom iteracije, ne zelimo
        # mijenjati listu po kojoj upravo iteriramo
        dead: list[WebSocket] = []
        for connection in list(connections):
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for connection in dead:
            if connection in connections:
                connections.remove(connection)
        if dead:
            logger.info("WS_PRUNED_DEAD_CONNECTIONS count=%d", len(dead))

    async def _broadcast_admin_async(self, message: dict) -> None:
        await self._send_to(self.admin_connections, message)

    async def _broadcast_all_async(self, message: dict) -> None:
        await self._send_to(self.admin_connections, message)
        await self._send_to(self.status_connections, message)

    def broadcast_admin(self, message: dict) -> None:
        """Samo admin dashboardu - npr. vote_count (poglavlje 16, admin
        podaci koji terminalu nisu potrebni)."""
        if self._loop is None or not self.admin_connections:
            return
        asyncio.run_coroutine_threadsafe(self._broadcast_admin_async(message), self._loop)

    def broadcast_all(self, message: dict) -> None:
        """Admin dashboardu I glasackim terminalima - SAMO za evente bez
        ikakvog osjetljivog sadrzaja (RULE 08/09), npr. election_changed."""
        if self._loop is None or not (self.admin_connections or self.status_connections):
            return
        asyncio.run_coroutine_threadsafe(self._broadcast_all_async(message), self._loop)


manager = ConnectionManager()
