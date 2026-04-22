"""add performance and retraining events

Revision ID: 20260422_0003
Revises: 20260422_0002
Create Date: 2026-04-22 17:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "20260422_0003"
down_revision: str | None = "20260422_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("prediction_logs", sa.Column("actual_label", sa.Boolean(), nullable=True))

    op.create_table(
        "performance_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("sample_size", sa.Integer(), nullable=False),
        sa.Column("positive_rate", sa.Float(), nullable=False),
        sa.Column("accuracy", sa.Float(), nullable=False),
        sa.Column("precision", sa.Float(), nullable=True),
        sa.Column("recall", sa.Float(), nullable=True),
        sa.Column("f1_score", sa.Float(), nullable=True),
        sa.Column("roc_auc", sa.Float(), nullable=True),
        sa.Column("performance_below_threshold", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["batch_id"],
            ["batches.id"],
            name=op.f("fk_performance_metrics_batch_id_batches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_performance_metrics")),
    )
    op.create_index(
        op.f("ix_performance_metrics_batch_id"),
        "performance_metrics",
        ["batch_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_performance_metrics_model_version"),
        "performance_metrics",
        ["model_version"],
        unique=False,
    )

    op.create_table(
        "retraining_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("model_version_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("triggered_by", sa.String(length=32), nullable=False),
        sa.Column("drift_score", sa.Float(), nullable=True),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["model_version_id"],
            ["model_versions.id"],
            name=op.f("fk_retraining_events_model_version_id_model_versions"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retraining_events")),
    )
    op.create_index(
        op.f("ix_retraining_events_model_version_id"),
        "retraining_events",
        ["model_version_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_retraining_events_model_version_id"), table_name="retraining_events")
    op.drop_table("retraining_events")
    op.drop_index(op.f("ix_performance_metrics_model_version"), table_name="performance_metrics")
    op.drop_index(op.f("ix_performance_metrics_batch_id"), table_name="performance_metrics")
    op.drop_table("performance_metrics")
    op.drop_column("prediction_logs", "actual_label")
