"""
Jednokratna skripta za kreiranje admin korisnika (poglavlje 16 - postoji
jedan administratorski korisnik).

Pokreni iz backend/ foldera, s aktivnim venv-om:
    python scripts/create_admin.py
"""

import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.auth.security import hash_password  # noqa: E402
from app.database.base import SessionLocal  # noqa: E402
from app.database.models import AdminUser  # noqa: E402


def main():
    username = input("Korisnicko ime za admina: ").strip()
    password = getpass.getpass("Lozinka: ")
    password_confirm = getpass.getpass("Ponovi lozinku: ")

    if not username or not password:
        print("Korisnicko ime i lozinka ne smiju biti prazni.")
        return

    if password != password_confirm:
        print("Lozinke se ne podudaraju.")
        return

    db = SessionLocal()
    try:
        existing = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing:
            print(f"Admin '{username}' vec postoji.")
            return

        admin = AdminUser(username=username, password_hash=hash_password(password))
        db.add(admin)
        db.commit()
        print(f"Admin '{username}' je uspjesno kreiran.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
