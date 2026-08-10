from datetime import UTC, datetime, timedelta
from typing import Any, Literal
from uuid import UUID

import jwt

TokenType = Literal["access", "refresh"]


class TokenError(Exception):
    pass


def create_token(
    *,
    user_id: UUID,
    role: str,
    tenant_id: str,
    token_type: TokenType,
    secret: str,
    algorithm: str,
    expire_minutes: int,
) -> tuple[str, datetime]:
    now = datetime.now(UTC)
    expires_at = now + timedelta(minutes=expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "tenant_id": tenant_id,
        "type": token_type,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, secret, algorithm=algorithm)
    return token, expires_at


def decode_token(
    token: str,
    *,
    expected_type: TokenType,
    secret: str,
    algorithm: str,
) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError(str(exc)) from exc

    if payload.get("type") != expected_type:
        raise TokenError(f"expected a {expected_type} token")

    return payload
