"""
SQLAlchemy modeli prema PROJECT_SPECIFICATION_v1.1.md (poglavlja 17-21, 34).

Namjerno NE postoji:
- tablica `voters` (RULE 01)
- `voter_id` / `issued_to` / `person_id` u vote_tokens (RULE 02)
- `token_id` / `token_hash` / `voter_id` u votes (RULE 03)
- ikakva veza vote_tokens <-> votes (poglavlje 7, 18)
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.database.base import Base


def gen_uuid():
    return uuid.uuid4()


class ElectionStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class StationStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class DeviceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class TokenStatus(str, enum.Enum):
    # RULE 05 - token moze prijeci samo AVAILABLE -> USED
    AVAILABLE = "AVAILABLE"
    USED = "USED"


class Election(Base):
    __tablename__ = "elections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    name = Column(String(255), nullable=False)
    status = Column(
        SAEnum(ElectionStatus, name="election_status"),
        nullable=False,
        default=ElectionStatus.DRAFT,
    )
    # 34.1 - javni kljuc para generiranog pri otvaranju izbora.
    # Privatni kljuc se NIKAD ne sprema ovdje - admin ga cuva izvan sustava.
    public_key = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    # FAZA 9 (dopuna) - zakazano automatsko otvaranje/zatvaranje (pozadinski
    # zadatak u app/scheduler.py provjerava ova polja). Kad je
    # scheduled_open_at postavljen VEC PRI KREIRANJU izbora, par kljuceva se
    # generira ODMAH (ne cekajuci stvarno otvaranje) jer administrator mora
    # biti prisutan da sacuva privatni kljuc (34.1) - stvarno otvaranje u
    # zakazano vrijeme tad je samo promjena statusa, bez ikoga prisutnog.
    scheduled_open_at = Column(DateTime(timezone=True), nullable=True)
    scheduled_close_at = Column(DateTime(timezone=True), nullable=True)

    candidates = relationship("Candidate", back_populates="election", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="election", cascade="all, delete-orphan")


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    display_order = Column(Integer, nullable=False, default=0)

    election = relationship("Election", back_populates="candidates")


class PollingStation(Base):
    __tablename__ = "polling_stations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    # FAZA 9 (dopuna) - zupanija biralista, koristi se za grupiranje rezultata
    # na Tally ekranu (po zupaniji i po NUTS2 regiji, izvedeno iz zupanije u
    # kodu - vidi app/elections/regions.py). Nullable jer starija/rucno
    # dodana biralista mozda nemaju popunjeno.
    zupanija = Column(String(100), nullable=True)
    # broj birača koji pripadaju stanici - NE digitalni popis osoba (poglavlje 19)
    registered_voters = Column(Integer, nullable=False)
    status = Column(
        SAEnum(StationStatus, name="station_status"),
        nullable=False,
        default=StationStatus.ACTIVE,
    )

    devices = relationship("Device", back_populates="station", cascade="all, delete-orphan")
    vote_tokens = relationship("VoteToken", back_populates="station", cascade="all, delete-orphan")

    @property
    def region(self) -> str | None:
        # FAZA 9 (dopuna) - izvedeno iz zupanije, ne sprema se u bazu (vidi
        # app/elections/regions.py). Lokalni import da models.py (najniži
        # sloj) ostane bez tvrde ovisnosti o app/elections na razini modula.
        from app.elections.regions import get_region

        return get_region(self.zupanija)


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    station_id = Column(UUID(as_uuid=True), ForeignKey("polling_stations.id", ondelete="CASCADE"), nullable=False)
    device_code = Column(String(50), unique=True, nullable=False)
    # 34.2 - hash device API kljuca (isti princip kao token_hash), nikad plaintext
    device_key_hash = Column(Text, nullable=False)
    status = Column(
        SAEnum(DeviceStatus, name="device_status"),
        nullable=False,
        default=DeviceStatus.ACTIVE,
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    station = relationship("PollingStation", back_populates="devices")


class VoteToken(Base):
    __tablename__ = "vote_tokens"
    __table_args__ = (UniqueConstraint("token_hash", name="uq_vote_tokens_token_hash"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    station_id = Column(UUID(as_uuid=True), ForeignKey("polling_stations.id", ondelete="CASCADE"), nullable=False)
    # RULE 04 - sprema se samo hash, nikad sirovi token
    token_hash = Column(String(128), nullable=False)
    status = Column(
        SAEnum(TokenStatus, name="token_status"),
        nullable=False,
        default=TokenStatus.AVAILABLE,
    )
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    station = relationship("PollingStation", back_populates="vote_tokens")


Index("ix_vote_tokens_token_hash", VoteToken.token_hash)


class Vote(Base):
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    election_id = Column(UUID(as_uuid=True), ForeignKey("elections.id", ondelete="CASCADE"), nullable=False)
    station_id = Column(UUID(as_uuid=True), ForeignKey("polling_stations.id", ondelete="RESTRICT"), nullable=False)
    # 34.1 - hibridna enkripcija (AES-256-GCM + RSA/ECIES wrap), base64, sve u jednom polju
    encrypted_vote = Column(Text, nullable=False)
    # 34.1 - lancani hash: SHA-256(ciphertext || prev_hash || election_id)
    integrity_hash = Column(String(128), nullable=False)
    prev_hash = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    election = relationship("Election", back_populates="votes")


Index("ix_votes_election_id", Vote.election_id)
Index("ix_votes_station_id", Vote.station_id)


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    username = Column(String(100), unique=True, nullable=False)
    # 34.4 - Argon2id
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    audit_logs = relationship("AuditLog", back_populates="admin_user")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=gen_uuid)
    # npr. ADMIN_LOGIN, ELECTION_OPENED, VOTE_ACCEPTED, INVALID_TOKEN_ATTEMPT... (poglavlje 22)
    event_type = Column(String(100), nullable=False)
    admin_user_id = Column(UUID(as_uuid=True), ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)
    station_id = Column(UUID(as_uuid=True), ForeignKey("polling_stations.id", ondelete="SET NULL"), nullable=True)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)
    # POGLAVLJE 22/23 - u ovo polje NIKAD ne smije zavrsiti raw token, token_hash,
    # identitet biraca, OIB, sadrzaj glasa niti token->vote veza.
    event_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    admin_user = relationship("AdminUser", back_populates="audit_logs")


Index("ix_audit_logs_event_type", AuditLog.event_type)
Index("ix_audit_logs_created_at", AuditLog.created_at)
