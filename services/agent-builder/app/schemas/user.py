import uuid

from fastapi_users import schemas
from pydantic import BaseModel
from shared.auth.roles import Role


class UserRead(schemas.BaseUser[uuid.UUID]):
    role: Role


class UserCreate(schemas.BaseUserCreate):
    role: Role = Role.ANALYST


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str
