"""Password hashing, signed V1-compatible session tokens and cookie settings."""

import base64
import hashlib
import hmac
import json
import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

SESSION_SECONDS = 24 * 60 * 60
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() != "false"
COOKIE_NAME = "__Host-vr_session" if COOKIE_SECURE else "vr_session"


def _business_timezone() -> ZoneInfo:
    return ZoneInfo(os.environ.get("TZ", "Europe/Paris"))


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def _signing_key() -> bytes:
    secret = os.environ.get("AUTH_TOKEN_SECRET", "").encode()
    if len(secret) < 32:
        raise RuntimeError("AUTH_TOKEN_SECRET must contain at least 32 bytes.")
    return secret


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.scrypt(
        password.encode(), salt=salt, n=2**15, r=8, p=1, dklen=64, maxmem=64 * 1024 * 1024
    )
    return f"scrypt$32768$8$1${_b64encode(salt)}${_b64encode(derived)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, n, r, p, salt_text, digest_text = encoded.split("$")
        if scheme != "scrypt":
            return False
        expected = _b64decode(digest_text)
        actual = hashlib.scrypt(
            password.encode(),
            salt=_b64decode(salt_text),
            n=int(n),
            r=int(r),
            p=int(p),
            dklen=len(expected),
            maxmem=64 * 1024 * 1024,
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_session_token(
    *, user_id: str, email: str, session_id: str, session_version: int
) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires = now + timedelta(seconds=SESSION_SECONDS)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "sessionVersion": session_version,
        "jourConnexion": now.astimezone(_business_timezone()).date().isoformat(),
        "sid": session_id,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
    }
    header_part = _b64encode(json.dumps(header, separators=(",", ":")).encode())
    payload_part = _b64encode(json.dumps(payload, separators=(",", ":")).encode())
    body = f"{header_part}.{payload_part}"
    signature = hmac.new(_signing_key(), body.encode(), hashlib.sha256).digest()
    return f"{body}.{_b64encode(signature)}", expires


def decode_session_token(token: str) -> dict[str, Any] | None:
    try:
        header_part, payload_part, signature_part = token.split(".")
        body = f"{header_part}.{payload_part}"
        signature = _b64decode(signature_part)
        expected = hmac.new(_signing_key(), body.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            return None
        header = json.loads(_b64decode(header_part))
        claims = json.loads(_b64decode(payload_part))
        if header != {"alg": "HS256", "typ": "JWT"}:
            return None
        now = datetime.now(UTC)
        expires_at = claims.get("exp")
        if not isinstance(expires_at, int) or expires_at <= int(now.timestamp()):
            return None
        if not all(isinstance(claims.get(name), str) for name in ("sub", "sid", "email")):
            return None
        if not isinstance(claims.get("sessionVersion"), int):
            return None
        connection_day = claims.get("jourConnexion")
        if connection_day != now.astimezone(_business_timezone()).date().isoformat():
            return None
        return claims
    except (RuntimeError, ValueError, TypeError, json.JSONDecodeError):
        return None


def new_session_id() -> str:
    return str(uuid.uuid4())
