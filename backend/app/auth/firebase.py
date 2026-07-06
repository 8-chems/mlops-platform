"""Firebase Admin SDK initialization and ID token verification."""
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

from app.core.config import get_settings

settings = get_settings()

_app = None


def get_firebase_app():
    global _app
    if _app is None:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        _app = firebase_admin.initialize_app(cred)
    return _app


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token from the frontend Google Sign-In flow.

    Returns the decoded token containing uid, email, name, etc.
    Raises firebase_admin.auth.InvalidIdTokenError on failure.
    """
    get_firebase_app()
    return firebase_auth.verify_id_token(id_token)
