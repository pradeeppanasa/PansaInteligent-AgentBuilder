from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi_users.exceptions import UserNotExists
from shared.auth.jwt import TokenError, decode_token
from shared.auth.roles import Role

from app.core.config import settings
from app.core.users import UserManager, get_user_manager
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_active_user(
    token: str | None = Depends(oauth2_scheme),
    user_manager: UserManager = Depends(get_user_manager),
) -> User:
    if token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")

    try:
        payload = decode_token(
            token,
            expected_type="access",
            secret=settings.JWT_SECRET,
            algorithm=settings.JWT_ALGORITHM,
        )
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc)) from exc

    try:
        user = await user_manager.get(UUID(payload["sub"]))
    except UserNotExists as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found") from exc

    if not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Inactive user")

    if payload.get("tenant_id") != user.tenant_id:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token tenant mismatch")

    return user


def require_role(*allowed_roles: Role):
    async def dependency(user: User = Depends(get_current_active_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return user

    return dependency
