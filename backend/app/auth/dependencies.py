import uuid

import jwt as pyjwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.security import decode_access_token
from app.errors import AppError

# auto_error=False - sami bacamo AppError (pa ide kroz nas error wrapper,
# poglavlje 27) umjesto da FastAPI vrati svoj default 403 format
bearer_scheme = HTTPBearer(auto_error=False)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Neautoriziran pristup."):
        super().__init__("UNAUTHORIZED", message, status_code=401)


def get_current_admin_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> uuid.UUID:
    """FastAPI dependency - provjerava Bearer JWT.

    Koristi se za zastitu svih admin endpointa (poglavlje 24 - Autorizacija).
    Registracija kroz HTTPBearer omogucuje jedan "Authorize" gumb u Swagger
    UI (/docs) umjesto rucnog upisivanja headera na svaki endpoint.
    """
    if credentials is None:
        raise UnauthorizedError()

    try:
        payload = decode_access_token(credentials.credentials)
    except pyjwt.PyJWTError:
        raise UnauthorizedError("Token nije valjan ili je istekao.")

    try:
        return uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise UnauthorizedError("Token ima neispravan sadrzaj.")
