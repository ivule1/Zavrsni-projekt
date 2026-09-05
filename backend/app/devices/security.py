"""
Device API kljucevi (poglavlje 34.2) - isti princip kao token_hash:
sprema se samo hash, nikad sirovi kljuc.
"""

import hashlib
import hmac
import os
import secrets

DEVICE_KEY_PEPPER = os.getenv("DEVICE_KEY_PEPPER", "dev-pepper-change-me")


def generate_device_api_key() -> str:
    return secrets.token_urlsafe(32)


def hash_device_key(raw_key: str) -> str:
    return hmac.new(DEVICE_KEY_PEPPER.encode(), raw_key.encode(), hashlib.sha256).hexdigest()
