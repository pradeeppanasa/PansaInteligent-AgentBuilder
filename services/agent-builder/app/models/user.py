from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from shared.auth.roles import Role
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    role: Mapped[str] = mapped_column(String(20), nullable=False, default=Role.ANALYST)
    tenant_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
