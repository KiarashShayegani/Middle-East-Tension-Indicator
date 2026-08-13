"""Plotly chart helpers for METI."""

from __future__ import annotations

from typing import Any

import plotly.graph_objects as go

from meti.config import Settings, get_settings


def create_tension_gauge(score: int, settings: Settings | None = None) -> go.Figure:
    """Create a clean dark-themed tension gauge."""
    settings = settings or get_settings()
    steps = []
    for step in settings.gauge.steps:
        steps.append(
            {
                "range": step.range,
                "color": step.color,
            }
        )

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            title={
                "text": "Tension Index",
                "font": {"size": 20, "color": "#e2e8f0", "family": "Inter, Arial"},
            },
            number={
                "font": {"size": 52, "color": "#f8fafc", "family": "Inter, Arial Black"},
                "suffix": "",
            },
            gauge={
                "axis": {
                    "range": [0, 100],
                    "tickwidth": 1,
                    "tickcolor": "#94a3b8",
                    "tickfont": {"color": "#94a3b8", "size": 11},
                },
                "bar": {"color": "#3b82f6", "thickness": 0.30},
                "bgcolor": "rgba(15, 23, 42, 0.45)",
                "borderwidth": 2,
                "bordercolor": "rgba(148, 163, 184, 0.25)",
                "steps": steps,
                "threshold": {
                    "line": {"color": "#f8fafc", "width": 3},
                    "thickness": 0.85,
                    "value": score,
                },
            },
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#e2e8f0"},
        height=320,
        margin=dict(t=50, b=20, l=25, r=25),
    )
    return fig


def create_history_chart(snapshots: list[dict[str, Any]]) -> go.Figure:
    """Simple line chart of historical tension scores."""
    if not snapshots:
        fig = go.Figure()
        fig.add_annotation(
            text="No historical data yet.<br>Data will appear after the first few refreshes.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 16, "color": "#94a3b8"},
        )
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=320,
            xaxis={"visible": False},
            yaxis={"visible": False},
        )
        return fig

    times = [s["ts"][:16].replace("T", " ") for s in snapshots]
    scores = [s["tension_score"] for s in snapshots]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=times,
            y=scores,
            mode="lines+markers",
            line={"color": "#3b82f6", "width": 2.5},
            marker={"size": 5, "color": "#60a5fa"},
            name="Tension Score",
            fill="tozeroy",
            fillcolor="rgba(59, 130, 246, 0.12)",
        )
    )

    # Reference lines
    for y, color, label in [
        (25, "rgba(16, 185, 129, 0.5)", "Calm"),
        (50, "rgba(250, 204, 21, 0.5)", "Elevated"),
        (75, "rgba(239, 68, 68, 0.5)", "Critical"),
    ]:
        fig.add_hline(
            y=y,
            line_dash="dot",
            line_color=color,
            annotation_text=label,
            annotation_position="right",
            annotation_font_color=color,
        )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.3)",
        font={"color": "#e2e8f0"},
        height=360,
        margin=dict(t=30, b=40, l=50, r=30),
        xaxis={
            "title": None,
            "gridcolor": "rgba(148, 163, 184, 0.15)",
            "tickangle": -30,
            "nticks": 8,
        },
        yaxis={
            "title": "Tension Score",
            "range": [0, 100],
            "gridcolor": "rgba(148, 163, 184, 0.15)",
        },
        showlegend=False,
    )
    return fig


def create_contribution_bar(contributions: dict[str, Any]) -> go.Figure:
    """Horizontal bar showing each asset's contribution to the raw index."""
    names = []
    values = []
    colors = []

    for ticker, info in contributions.items():
        names.append(f"{info['emoji']} {info['name']}")
        values.append(round(info["contribution"], 3))
        colors.append(info.get("color", "#3b82f6"))

    fig = go.Figure(
        go.Bar(
            x=values,
            y=names,
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.2f}" for v in values],
            textposition="outside",
            textfont={"color": "#e2e8f0", "size": 12},
        )
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(15, 23, 42, 0.25)",
        font={"color": "#e2e8f0", "size": 12},
        height=260,
        margin=dict(t=16, b=36, l=130, r=50),
        xaxis={
            "title": "Contribution to Raw Index",
            "gridcolor": "rgba(148, 163, 184, 0.12)",
            "zeroline": True,
            "zerolinecolor": "rgba(148, 163, 184, 0.35)",
            "zerolinewidth": 1,
        },
        yaxis={"title": None},
        showlegend=False,
    )
    return fig
