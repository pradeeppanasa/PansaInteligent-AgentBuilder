"""add tenant_id to users

Revision ID: 71dad4c23b9c
Revises: 6f6208ac1bb7
Create Date: 2026-08-10 18:15:24.757050

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "71dad4c23b9c"
down_revision: Union[str, None] = "6f6208ac1bb7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("tenant_id", sa.String(length=64), nullable=False, server_default="default"),
    )
    op.create_index(op.f("ix_users_tenant_id"), "users", ["tenant_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_users_tenant_id"), table_name="users")
    op.drop_column("users", "tenant_id")
