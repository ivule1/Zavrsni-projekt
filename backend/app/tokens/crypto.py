"""
Generiranje i hashiranje glasackih tokena (poglavlje 4-6, 34.5).

RULE 04 - u bazi se sprema SAMO hash, nikad sirovi token.
RULE 07 - sirovi token se ne smije zapisivati u logove (ni ovaj modul to
ne radi - generate_raw_token() vraca vrijednost samo pozivatelju).
"""

import base64
import hashlib
import hmac
import os
import secrets

TOKEN_HASH_PEPPER = os.getenv("TOKEN_HASH_PEPPER", "dev-token-pepper-change-me")


def generate_raw_token() -> str:
    """128-bitni nasumican token, Base32 enkodiran, grupiran u blokove od 5
    znakova radi citljivosti pri fizickom rukovanju (34.5). Base32 alfabet
    (A-Z, 2-7) namjerno ne koristi znamenke 0/1 pa nema zabune s O/I.
    """
    raw_bytes = secrets.token_bytes(16)  # 128 bit
    encoded = base64.b32encode(raw_bytes).decode("ascii").rstrip("=")
    grouped = "-".join(encoded[i : i + 5] for i in range(0, len(encoded), 5))
    return grouped


def normalize_token(raw_token: str) -> str:
    """Uklanja razmake/crtice, pretvara u velika slova - da unos s razlicitim
    formatiranjem (s crticama ili bez) hashira na isti nacin."""
    return raw_token.replace("-", "").replace(" ", "").strip().upper()


def hash_token(raw_token: str) -> str:
    """HMAC-SHA256 s poslužiteljskim pepper-om (34.4 napomena - token vec
    ima visoku entropiju, treba brz hash za lookup, ne Argon2)."""
    normalized = normalize_token(raw_token)
    return hmac.new(TOKEN_HASH_PEPPER.encode(), normalized.encode(), hashlib.sha256).hexdigest()
