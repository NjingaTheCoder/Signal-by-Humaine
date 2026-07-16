"""add source column to jobs_board

Revision ID: 002
Revises: 001
Create Date: 2026-07-16

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("jobs_board", sa.Column("source", sa.String(40), nullable=True))
    op.create_index("idx_jobs_board_source", "jobs_board", ["source"])


def downgrade() -> None:
    op.drop_index("idx_jobs_board_source", table_name="jobs_board")
    op.drop_column("jobs_board", "source")
