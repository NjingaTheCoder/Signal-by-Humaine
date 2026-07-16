"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-07-09

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "articles",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("url_hash", sa.CHAR(64), nullable=False, unique=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("snippet", sa.String(400)),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("categories", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("is_win", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("classified", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.create_index("idx_articles_pub", "articles", [sa.text("published_at DESC")])
    op.create_index("idx_articles_cat", "articles", ["categories"], postgresql_using="gin")

    op.create_table(
        "funding_rounds",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("source_url", sa.Text(), nullable=False, unique=True),
        sa.Column("company", sa.Text(), nullable=False),
        sa.Column("amount_usd", sa.Numeric(14, 0)),
        sa.Column("round", sa.String(40)),
        sa.Column("category", sa.String(60)),
        sa.Column("investors", postgresql.ARRAY(sa.Text())),
        sa.Column("announced_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("source", sa.String(80), nullable=False),
        sa.Column("parse_method", sa.String(10), nullable=False),
    )

    op.create_table(
        "tenders",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("ocid", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("buyer", sa.Text()),
        sa.Column("value_amount", sa.Numeric(14, 2)),
        sa.Column("value_currency", sa.String(3)),
        sa.Column("cpv_codes", postgresql.ARRAY(sa.Text())),
        sa.Column("region", sa.String(8), nullable=False),
        sa.Column("stage", sa.String(20), nullable=False),
        sa.Column("deadline", sa.TIMESTAMP(timezone=True)),
        sa.Column("source_url", sa.Text()),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )

    op.create_table(
        "quotes",
        sa.Column("symbol", sa.String(12), primary_key=True),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("grp", sa.String(12), nullable=False),
        sa.Column("price", sa.Numeric(12, 2)),
        sa.Column("change_pct", sa.Numeric(8, 3)),
        sa.Column("quoted_at", sa.TIMESTAMP(timezone=True)),
    )

    op.create_table(
        "briefings",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("week_of", sa.Date(), nullable=False),
        sa.Column("headline", sa.Text(), nullable=False),
        sa.Column("section_moved", sa.Text(), nullable=False),
        sa.Column("section_tape", sa.Text(), nullable=False),
        sa.Column("section_next", sa.Text(), nullable=False),
        sa.Column("benchmark_value", sa.String(24)),
        sa.Column("benchmark_label", sa.Text()),
        sa.Column("status", sa.String(10), nullable=False, server_default="draft"),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True)),
    )

    op.create_table(
        "jobs_board",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("role", sa.Text(), nullable=False),
        sa.Column("lab", sa.String(40)),
        sa.Column("location", sa.String(80)),
        sa.Column("type", sa.String(20)),
        sa.Column("apply_url", sa.Text()),
        sa.Column("active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "resources",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("url", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("excerpt", sa.String(400)),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )

    op.create_table(
        "subscribers",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("email", postgresql.CITEXT(), nullable=False, unique=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.Column("hubspot_synced", sa.Boolean(), server_default="false"),
    )

    op.create_table(
        "job_runs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("job", sa.String(40), nullable=False),
        sa.Column("started", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("finished", sa.TIMESTAMP(timezone=True)),
        sa.Column("rows_written", sa.Integer(), server_default="0"),
        sa.Column("ok", sa.Boolean()),
        sa.Column("error", sa.Text()),
    )

    op.create_table(
        "source_health",
        sa.Column("source", sa.String(80), primary_key=True),
        sa.Column("last_ok", sa.TIMESTAMP(timezone=True)),
        sa.Column("last_error", sa.Text()),
        sa.Column("consecutive_failures", sa.Integer(), server_default="0"),
        sa.Column("fetch_mode", sa.String(12), server_default="direct"),
    )


def downgrade() -> None:
    op.drop_table("source_health")
    op.drop_table("job_runs")
    op.drop_table("subscribers")
    op.drop_table("resources")
    op.drop_table("jobs_board")
    op.drop_table("briefings")
    op.drop_table("quotes")
    op.drop_table("tenders")
    op.drop_table("funding_rounds")
    op.drop_index("idx_articles_cat", table_name="articles")
    op.drop_index("idx_articles_pub", table_name="articles")
    op.drop_table("articles")
