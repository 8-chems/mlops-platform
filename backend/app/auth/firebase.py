"""Firebase Admin SDK initialization and ID token verification."""
import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, auth as firebase_auth

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

_app = None


def get_firebase_app():
    global _app
    if _app is None:
        firebase_creds_json = os.environ.get("FIREBASE_CREDENTIALS")
        try:
            if firebase_creds_json:
                logger.info("Initializing Firebase app from FIREBASE_CREDENTIALS env var")
                cred = credentials.Certificate(json.loads(firebase_creds_json))
            else:
                logger.info(
                    "FIREBASE_CREDENTIALS not set, falling back to file path: %s",
                    settings.firebase_credentials_path,
                )
                cred = credentials.Certificate(settings.firebase_credentials_path)
            _app = firebase_admin.initialize_app(cred)
            logger.info("Firebase app initialized successfully, project_id=%s", cred.project_id)
        except Exception:
            logger.exception("Failed to initialize Firebase app")
            raise
    return _app


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token from the frontend Google Sign-In flow.

    Returns the decoded token containing uid, email, name, etc.
    Raises firebase_admin.auth.InvalidIdTokenError on failure.
    """
    get_firebase_app()
    logger.info("Verifying Firebase ID token, length=%d", len(id_token) if id_token else 0)
    try:
        decoded = firebase_auth.verify_id_token(id_token)
        logger.info("Token verified successfully for uid=%s", decoded.get("uid"))
        return decoded
    except firebase_auth.ExpiredIdTokenError:
        logger.warning("Firebase token verification failed: token expired")
        raise
    except firebase_auth.InvalidIdTokenError as e:
        logger.warning("Firebase token verification failed: invalid token - %s", e)
        raise
    except firebase_auth.CertificateFetchError as e:
        logger.error("Firebase token verification failed: could not fetch certs - %s", e)
        raise
    except Exception:
        logger.exception("Unexpected error during Firebase token verification")
        raise