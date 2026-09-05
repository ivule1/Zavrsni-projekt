import uuid

from pydantic import BaseModel


class VoteCastRequest(BaseModel):
    token: str
    candidate_id: uuid.UUID


class VoteCastResponse(BaseModel):
    accepted: bool
    vote_id: uuid.UUID
