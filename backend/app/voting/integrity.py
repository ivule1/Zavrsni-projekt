"""
Lancani integrity hash za glasove unutar jednog izbora (poglavlje 34.1).

Svaki glas ukljucuje hash prethodnog glasa u istom electionu - naknadna
izmjena ili brisanje bilo kojeg retka lomi lanac i odmah je uocljivo, bez
potrebe za dekripcijom bilo cega.
"""

import hashlib


def compute_integrity_hash(ciphertext_b64: str, prev_hash: str | None, election_id: str) -> str:
    payload = f"{ciphertext_b64}|{prev_hash or ''}|{election_id}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_chain(votes: list[tuple[str, str | None, str]], election_id: str) -> bool:
    """FAZA 9 (Tally) - provjerava da lanac integrity_hash-eva nije prekinut.

    `votes` mora biti VEC SORTIRAN po created_at RASTUCE (redoslijed
    unosenja, ne smije se promijesati prije ovog poziva - shuffle za prikaz
    rezultata radi se tek NAKON ove provjere, na kopiji podataka).

    Svaki element je (encrypted_vote, prev_hash, integrity_hash). Vraca
    False cim bilo koji redak ne odgovara ocekivanom lancu - to znaci da je
    neki glas naknadno izmijenjen ili obrisan (poglavlje 25 - integritet).
    """
    expected_prev = None
    for encrypted_vote, prev_hash, integrity_hash in votes:
        if prev_hash != expected_prev:
            return False
        if compute_integrity_hash(encrypted_vote, prev_hash, election_id) != integrity_hash:
            return False
        expected_prev = integrity_hash
    return True
