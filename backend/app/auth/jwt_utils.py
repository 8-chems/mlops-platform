from datetime import datetime, timedelta
import logging
import uuid

from jose import jwt, JWTError, ExpiredSignatureError, JWTClaimsError

from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    if not settings.jwt_secret_key:
        logger.error("JWT_SECRET_KEY is missing/empty when creating access token")
        raise RuntimeError("JWT secret key is not configured")

    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "exp": expire}
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    logger.info("Access token created for user_id=%s, role=%s, expires=%s", user_id, role, expire)
    return token


def decode_access_token(token: str) -> dict | None:
    if not settings.jwt_secret_key:
        logger.error("JWT_SECRET_KEY is missing/empty when decoding access token")
        return None

    if not token:
        logger.warning("decode_access_token called with empty/None token")
        return None

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        logger.info("Access token decoded OK for sub=%s", payload.get("sub"))
        return payload
    except ExpiredSignatureError:
        logger.warning("Access token decode failed: EXPIRED")
        return None
    except JWTClaimsError as e:
        logger.warning("Access token decode failed: invalid claims - %s", e)
        return None
    except JWTError as e:
        logger.warning("Access token decode failed: %s (secret/algorithm mismatch or malformed token)", e)
        return None