"""add batch request metadata

Revision ID: 20260422_0002
Revises: 20260422_0001
Create Date: 2026-04-22 00:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260422_0002"
down_revision: str | None = "20260422_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("batches", sa.Column("request_metadata", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("batches", "request_metadata")
