from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from firebase_admin import auth as firebase_auth

from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import TokenResponse, UserOut
from app.auth.firebase import verify_firebase_token
from app.auth.jwt_utils import create_access_token
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


class GoogleLoginRequest(BaseModel):
    id_token: str


ADMIN_EMAIL_ALLOWLIST: set[str] = set()  # populate via env/secret manager in production


@router.post("/google", response_model=TokenResponse)
def login_with_google(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    """Exchange a Firebase ID token (from Google Sign-In on the frontend) for
    a platform-issued JWT, creating the user record on first login."""
    try:
        decoded = verify_firebase_token(payload.id_token)
    except (firebase_auth.InvalidIdTokenError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Google token")

    firebase_uid = decoded["uid"]
    email = decoded.get("email")
    name = decoded.get("name")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if user is None:
        role = UserRole.admin if email in ADMIN_EMAIL_ALLOWLIST else UserRole.client
        user = User(firebase_uid=firebase_uid, email=email, display_name=name, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
