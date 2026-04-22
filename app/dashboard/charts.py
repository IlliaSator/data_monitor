from __future__ import annotations

import pandas as pd
import plotly.express as px

from app.schemas.metrics import FeatureDriftHistoryPoint, GlobalDriftPoint


def build_global_drift_chart(points: list[GlobalDriftPoint]) -> str:
    if not points:
        return ""

    ordered_points = list(reversed([point.model_dump() for point in points]))
    dataframe = pd.DataFrame(ordered_points)
    figure = px.line(
        dataframe,
        x="created_at",
        y="global_drift_score",
        markers=True,
        title="Global Drift Score Over Time",
        labels={
            "created_at": "Captured At",
            "global_drift_score": "Drift Score",
        },
    )
    figure.update_traces(line_color="#b75d2b", marker_color="#2f6b4f")
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.9)",
        margin=dict(l=24, r=24, t=52, b=24),
    )
    return figure.to_html(full_html=False, include_plotlyjs="cdn")


def build_top_feature_chart(points: list[FeatureDriftHistoryPoint]) -> str:
    if not points:
        return ""

    latest_by_feature: dict[str, FeatureDriftHistoryPoint] = {}
    for point in points:
        existing = latest_by_feature.get(point.feature_name)
        if existing is None or point.created_at > existing.created_at:
            latest_by_feature[point.feature_name] = point

    top_points = [
        point.model_dump()
        for point in sorted(
            latest_by_feature.values(),
            key=lambda item: item.drift_score,
            reverse=True,
        )[:5]
    ]
    dataframe = pd.DataFrame(top_points)

    figure = px.bar(
        dataframe,
        x="feature_name",
        y="drift_score",
        title="Top Drifted Features",
        labels={"feature_name": "Feature", "drift_score": "Drift Score"},
        color="drift_score",
        color_continuous_scale=["#e7c7ac", "#b75d2b"],
    )
    figure.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(255,255,255,0.9)",
        margin=dict(l=24, r=24, t=52, b=24),
        coloraxis_showscale=False,
    )
    return figure.to_html(full_html=False, include_plotlyjs=False)
