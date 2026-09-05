from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.audit.service import log_event
from app.auth.dependencies import UnauthorizedError
from app.auth.schemas import LoginRequest, LoginResponse
from app.auth.security import create_access_token, verify_password
from app.database.base import get_db
from app.database.models import AdminUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    admin = db.query(AdminUser).filter(AdminUser.username == payload.username).first()

    if admin is None or not verify_password(payload.password, admin.password_hash):
        # namjerno ista poruka za "ne postoji" i "kriva lozinka" (ne otkrivamo koje korisnicko ime postoji)
        raise UnauthorizedError("Neispravno korisnicko ime ili lozinka.")

    token = create_access_token(str(admin.id), admin.username)
    log_event(db, "ADMIN_LOGIN", admin_user_id=admin.id)
    db.commit()

    return LoginResponse(access_token=token)
