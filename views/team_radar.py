import plotly.graph_objects as go
import streamlit as st

from hyroxator.models import _time_to_seconds
from views.charts import CHART_CONFIG
from views.data import (
    CATEGORY_COLORS,
    format_seconds,
    get_ranking,
    highlighted_team,
    team_selector,
)

SHORT = {
    "Burpee Broad Jumps": "BBJ",
    "Farmers Carry": "Farmers",
    "Lunges Sandbag": "Lunges",
    "Sandbag Lunges": "Lunges",
}


def _percentile(value: int, field: list[int]) -> float:
    if len(field) <= 1:
        return 100.0

    slower = sum(1 for other in field if other > value)
    return slower / (len(field) - 1) * 100


def _run_total(team) -> int | None:
    runs = [
        _time_to_seconds(event.time) for event in team.events if event.type == "run"
    ]

    if len(runs) != 8 or any(value is None for value in runs):
        return None

    return sum(value for value in runs if value is not None)


def render_team_radar() -> None:
    team_selector("radar")

    team_name = highlighted_team()

    if not team_name:
        st.info("Sélectionne une équipe ci-dessus pour afficher son profil.")
        return

    ranking = get_ranking()
    team = next(
        (item for item in ranking.ranking if item.team == team_name),
        None,
    )

    if team is None or not team.events:
        st.info(f"Aucun détail d'épreuve pour **{team_name}**.")
        return

    axes = []
    for event in sorted(team.events, key=lambda item: item.order):
        if event.type != "station":
            continue

        seconds = _time_to_seconds(event.time)
        if seconds is None:
            continue

        field = [value for _, _, value in ranking.stage_splits(event.order)]
        axes.append(
            (
                SHORT.get(event.name, event.name),
                _percentile(seconds, field),
                format_seconds(seconds),
            )
        )

    run_total = _run_total(team)
    if run_total is not None:
        run_field = [
            total
            for other in ranking.ranking
            for total in [_run_total(other)]
            if total is not None
        ]
        axes.append(
            ("Course", _percentile(run_total, run_field), format_seconds(run_total))
        )

    if len(axes) < 3:
        st.info(f"Pas assez de splits pour tracer le profil de **{team_name}**.")
        return

    st.caption("Percentile par épreuve (plus loin = plus rapide que le peloton).")

    labels = [axis[0] for axis in axes]
    values = [axis[1] for axis in axes]
    times = [axis[2] for axis in axes]

    color = CATEGORY_COLORS.get(team.gender, "#7C3AED")

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=[50] * (len(labels) + 1),
            theta=labels + labels[:1],
            mode="lines",
            line={"color": "rgba(0, 0, 0, 0.35)", "width": 1, "dash": "dot"},
            name="Médiane du peloton",
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatterpolar(
            r=values + values[:1],
            theta=labels + labels[:1],
            mode="lines+markers",
            fill="toself",
            fillcolor=f"rgba{(*_rgb(color), 0.25)}",
            line={"color": color, "width": 2},
            marker={"color": color, "size": 7},
            customdata=[[time, f"{value:.0f}"] for time, value in zip(times, values)]
            + [[times[0], f"{values[0]:.0f}"]],
            hovertemplate=(
                "<b>%{theta}</b><br>%{customdata[0]}<br>"
                "percentile %{customdata[1]}<extra></extra>"
            ),
            name=team_name,
        )
    )

    fig.update_layout(
        polar={
            "radialaxis": {
                "range": [0, 100],
                "tickvals": [25, 50, 75, 100],
                "tickfont": {"size": 9, "color": "#6B7280"},
                "gridcolor": "rgba(0, 0, 0, 0.08)",
            },
            "angularaxis": {
                "tickfont": {"size": 11},
                "rotation": 90,
                "direction": "clockwise",
            },
            "bgcolor": "rgba(0, 0, 0, 0)",
        },
        height=460,
        margin={"l": 40, "r": 40, "t": 40, "b": 40},
        paper_bgcolor="rgba(0, 0, 0, 0)",
        font={
            "family": "system-ui, -apple-system, sans-serif",
            "color": "#1F2937",
        },
        hoverlabel={
            "bgcolor": "white",
            "bordercolor": "rgba(0, 0, 0, 0.1)",
            "font_size": 13,
        },
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
        },
        dragmode=False,
    )

    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)


def _rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
