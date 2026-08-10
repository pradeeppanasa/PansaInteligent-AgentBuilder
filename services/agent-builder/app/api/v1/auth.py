from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.exceptions import UserAlreadyExists, UserNotExists
from shared.auth.jwt import TokenError, create_token, decode_token
from shared.auth.roles import Role

from app.core.config import settings
from app.core.security import get_current_active_user, require_role
from app.core.users import UserManager, get_user_manager
from app.models.user import User
from app.schemas.user import RefreshRequest, TokenResponse, UserCreate, UserRead

router = APIRouter()


def _issue_tokens(user: User) -> TokenResponse:
    access_token, _ = create_token(
        user_id=user.id,
        role=user.role,
        token_type="access",
        secret=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
        expire_minutes=settings.JWT_EXPIRE_MINUTES,
    )
    refresh_token, _ = create_token(
        user_id=user.id,
        role=user.role,
        token_type="refresh",
        secret=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
        expire_minutes=settings.JWT_REFRESH_EXPIRE_MINUTES,
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
) -> TokenResponse:
    user = await user_manager.authenticate(form)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid credentials")
    return _issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    body: RefreshRequest,
    user_manager: UserManager = Depends(get_user_manager),
) -> TokenResponse:
    try:
        payload = decode_token(
            body.refresh_token,
            expected_type="refresh",
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

    return _issue_tokens(user)


@router.get("/me", response_model=UserRead)
async def me(user: User = Depends(get_current_active_user)) -> User:
    return user


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role(Role.ADMIN))],
)
async def register(
    user_create: UserCreate,
    user_manager: UserManager = Depends(get_user_manager),
) -> User:
    try:
        return await user_manager.create(user_create)
    except UserAlreadyExists as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "User already exists") from exc
