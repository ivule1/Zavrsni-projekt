"""
Enkripcija glasa (poglavlje 34.1) - hibridna shema, "zapecacena kutija":

    nasumican AES-256-GCM kljuc enkriptira sadrzaj glasa
                    |
    taj AES kljuc se enkriptira RSA-OAEP javnim kljucem izbora
                    |
    encrypted_vote = "<b64 rsa-enkriptiran AES kljuc>.<b64 iv>.<b64 ciphertext+tag>"

encrypt_vote() se koristi u Fazi 6 (voting) - treba samo javni kljuc.
decrypt_vote() se koristi u Fazi 9 (Tally ekran) - treba privatni kljuc koji
admin unosi rucno, nikad se ne cuva u sustavu.
"""

import base64
import json
import os
import uuid

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_OAEP_PADDING = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None,
)


def encrypt_vote(public_key_pem: str, candidate_id: uuid.UUID) -> str:
    public_key = serialization.load_pem_public_key(public_key_pem.encode("utf-8"))

    plaintext = json.dumps(
        {
            "candidate_id": str(candidate_id),
            # nasumicni nonce - sprjecava da isti kandidat uvijek producira
            # prepoznatljiv ciphertext (AES-GCM IV je vec nasumican, ovo je
            # dodatna zastita na razini plaintexta)
            "nonce": base64.b64encode(os.urandom(16)).decode("ascii"),
        }
    ).encode("utf-8")

    aes_key = AESGCM.generate_key(bit_length=256)
    iv = os.urandom(12)
    ciphertext = AESGCM(aes_key).encrypt(iv, plaintext, None)

    encrypted_key = public_key.encrypt(aes_key, _OAEP_PADDING)

    return ".".join(
        [
            base64.b64encode(encrypted_key).decode("ascii"),
            base64.b64encode(iv).decode("ascii"),
            base64.b64encode(ciphertext).decode("ascii"),
        ]
    )


def decrypt_vote(private_key_pem: str, encrypted_vote: str) -> dict:
    private_key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)

    encrypted_key_b64, iv_b64, ciphertext_b64 = encrypted_vote.split(".")
    encrypted_key = base64.b64decode(encrypted_key_b64)
    iv = base64.b64decode(iv_b64)
    ciphertext = base64.b64decode(ciphertext_b64)

    aes_key = private_key.decrypt(encrypted_key, _OAEP_PADDING)
    plaintext = AESGCM(aes_key).decrypt(iv, ciphertext, None)
    return json.loads(plaintext.decode("utf-8"))
