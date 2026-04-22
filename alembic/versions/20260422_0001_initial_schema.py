"""initial schema

Revision ID: 20260422_0001
Revises:
Create Date: 2026-04-22 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260422_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

alert_severity = postgresql.ENUM("low", "medium", "high", name="alert_severity", create_type=False)
alert_status = postgresql.ENUM(
    "open",
    "acknowledged",
    "resolved",
    name="alert_status",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    alert_severity.create(bind, checkfirst=True)
    alert_status.create(bind, checkfirst=True)

    op.create_table(
        "baselines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("artifact_path", sa.Text(), nullable=False),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_baselines")),
        sa.UniqueConstraint("version", name=op.f("uq_baselines_version")),
    )
    op.create_index(op.f("ix_baselines_version"), "baselines", ["version"], unique=False)

    op.create_table(
        "model_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("artifact_uri", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("retrain_required", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_model_versions")),
        sa.UniqueConstraint("version", name=op.f("uq_model_versions_version")),
    )
    op.create_index(op.f("ix_model_versions_version"), "model_versions", ["version"], unique=False)

    op.create_table(
        "batches",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("baseline_version", sa.String(length=64), nullable=True),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column(
            "ingest_started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ingest_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("quality_summary", sa.JSON(), nullable=True),
        sa.Column("warnings", sa.JSON(), nullable=True),
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
        sa.PrimaryKeyConstraint("id", name=op.f("pk_batches")),
        sa.UniqueConstraint("external_id", name=op.f("uq_batches_external_id")),
    )
    op.create_index(
        op.f("ix_batches_baseline_version"),
        "batches",
        ["baseline_version"],
        unique=False,
    )
    op.create_index(op.f("ix_batches_external_id"), "batches", ["external_id"], unique=False)
    op.create_index(op.f("ix_batches_model_version"), "batches", ["model_version"], unique=False)

    op.create_table(
        "prediction_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.String(length=64), nullable=False),
        sa.Column("prediction", sa.Float(), nullable=False),
        sa.Column("prediction_label", sa.String(length=32), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("features", sa.JSON(), nullable=False),
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
            name=op.f("fk_prediction_logs_batch_id_batches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prediction_logs")),
    )
    op.create_index(
        op.f("ix_prediction_logs_batch_id"), "prediction_logs", ["batch_id"], unique=False
    )
    op.create_index(
        op.f("ix_prediction_logs_customer_id"),
        "prediction_logs",
        ["customer_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_prediction_logs_model_version"),
        "prediction_logs",
        ["model_version"],
        unique=False,
    )

    op.create_table(
        "drift_reports",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("batch_id", sa.Integer(), nullable=False),
        sa.Column("baseline_version", sa.String(length=64), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("global_drift_score", sa.Float(), nullable=False),
        sa.Column("drift_detected", sa.Boolean(), nullable=False),
        sa.Column("alert_triggered", sa.Boolean(), nullable=False),
        sa.Column("feature_count", sa.Integer(), nullable=False),
        sa.Column("report_path", sa.Text(), nullable=True),
        sa.Column("report_metadata", sa.JSON(), nullable=True),
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
            name=op.f("fk_drift_reports_batch_id_batches"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drift_reports")),
    )
    op.create_index(
        op.f("ix_drift_reports_baseline_version"),
        "drift_reports",
        ["baseline_version"],
        unique=False,
    )
    op.create_index(op.f("ix_drift_reports_batch_id"), "drift_reports", ["batch_id"], unique=False)
    op.create_index(
        op.f("ix_drift_reports_model_version"),
        "drift_reports",
        ["model_version"],
        unique=False,
    )

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drift_report_id", sa.Integer(), nullable=False),
        sa.Column("feature_name", sa.String(length=128), nullable=True),
        sa.Column("drift_score", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("severity", alert_severity, nullable=False),
        sa.Column("status", alert_status, nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
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
            ["drift_report_id"],
            ["drift_reports.id"],
            name=op.f("fk_alerts_drift_report_id_drift_reports"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_alerts")),
    )
    op.create_index(op.f("ix_alerts_drift_report_id"), "alerts", ["drift_report_id"], unique=False)
    op.create_index(op.f("ix_alerts_feature_name"), "alerts", ["feature_name"], unique=False)

    op.create_table(
        "feature_drift_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("drift_report_id", sa.Integer(), nullable=False),
        sa.Column("feature_name", sa.String(length=128), nullable=False),
        sa.Column("drift_score", sa.Float(), nullable=False),
        sa.Column("threshold", sa.Float(), nullable=False),
        sa.Column("is_drifted", sa.Boolean(), nullable=False),
        sa.Column("metric_details", sa.JSON(), nullable=True),
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
            ["drift_report_id"],
            ["drift_reports.id"],
            name=op.f("fk_feature_drift_metrics_drift_report_id_drift_reports"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_feature_drift_metrics")),
    )
    op.create_index(
        op.f("ix_feature_drift_metrics_drift_report_id"),
        "feature_drift_metrics",
        ["drift_report_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_feature_drift_metrics_feature_name"),
        "feature_drift_metrics",
        ["feature_name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_feature_drift_metrics_feature_name"), table_name="feature_drift_metrics")
    op.drop_index(
        op.f("ix_feature_drift_metrics_drift_report_id"),
        table_name="feature_drift_metrics",
    )
    op.drop_table("feature_drift_metrics")

    op.drop_index(op.f("ix_alerts_feature_name"), table_name="alerts")
    op.drop_index(op.f("ix_alerts_drift_report_id"), table_name="alerts")
    op.drop_table("alerts")

    op.drop_index(op.f("ix_drift_reports_model_version"), table_name="drift_reports")
    op.drop_index(op.f("ix_drift_reports_batch_id"), table_name="drift_reports")
    op.drop_index(op.f("ix_drift_reports_baseline_version"), table_name="drift_reports")
    op.drop_table("drift_reports")

    op.drop_index(op.f("ix_prediction_logs_model_version"), table_name="prediction_logs")
    op.drop_index(op.f("ix_prediction_logs_customer_id"), table_name="prediction_logs")
    op.drop_index(op.f("ix_prediction_logs_batch_id"), table_name="prediction_logs")
    op.drop_table("prediction_logs")

    op.drop_index(op.f("ix_batches_model_version"), table_name="batches")
    op.drop_index(op.f("ix_batches_external_id"), table_name="batches")
    op.drop_index(op.f("ix_batches_baseline_version"), table_name="batches")
    op.drop_table("batches")

    op.drop_index(op.f("ix_model_versions_version"), table_name="model_versions")
    op.drop_table("model_versions")

    op.drop_index(op.f("ix_baselines_version"), table_name="baselines")
    op.drop_table("baselines")

    bind = op.get_bind()
    alert_status.drop(bind, checkfirst=True)
    alert_severity.drop(bind, checkfirst=True)
