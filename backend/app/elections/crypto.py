"""
Generiranje asimetricnog para kljuceva za enkripciju glasova (poglavlje 34.1).

"Zapecacena kutija" model: javni kljuc se sprema u elections.public_key i
koristi se za enkripciju svakog glasa (Faza 6). Privatni kljuc se NIKAD ne
sprema - vraca se pozivatelju SAMO jednom, u trenutku generiranja, da ga
administrator sacuva izvan sustava. Koristi se opet tek na Tally ekranu
(Faza 9), rucno unesen, samo u memoriji.
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_election_keypair() -> tuple[str, str]:
    """Vraca (public_key_pem, private_key_pem)."""
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return public_pem, private_pem
