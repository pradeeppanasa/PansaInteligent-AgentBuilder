import structlog
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.exceptions import UserAlreadyExists
from shared.auth.roles import Role
from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.users import UserManager
from app.models.user import User
from app.schemas.user import UserCreate

logger = structlog.get_logger()


async def seed_bootstrap_admin() -> None:
    if not settings.BOOTSTRAP_ADMIN_EMAIL or not settings.BOOTSTRAP_ADMIN_PASSWORD:
        return

    async with AsyncSessionLocal() as session:
        existing_admin = await session.scalar(select(User).where(User.role == Role.ADMIN))
        if existing_admin is not None:
            return

        user_db = SQLAlchemyUserDatabase(session, User)
        user_manager = UserManager(user_db)
        try:
            await user_manager.create(
                UserCreate(
                    email=settings.BOOTSTRAP_ADMIN_EMAIL,
                    password=settings.BOOTSTRAP_ADMIN_PASSWORD,
                    role=Role.ADMIN,
                )
            )
            logger.info("bootstrap_admin_created", email=settings.BOOTSTRAP_ADMIN_EMAIL)
        except UserAlreadyExists:
            logger.info("bootstrap_admin_already_exists")
