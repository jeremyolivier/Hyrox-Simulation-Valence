import plotly.graph_objects as go
import polars as pl
import streamlit as st

from hyroxator.models import _time_to_seconds
from views.charts import CHART_CONFIG
from views.data import (
    format_seconds,
    get_ranking,
    highlighted_team,
    team_selector,
)
from views.standards import STATION_COLORS

RUN_COLOR = "#64748B"

SHORT_NAMES = {"Burpee Broad Jumps": "BBJ"}


def _splits(events):
    rows = []
    cursor = 0
    station_index = 0

    for event in events:
        seconds = _time_to_seconds(event.time)

        if seconds is None:
            continue

        if event.type == "run":
            color = RUN_COLOR
        else:
            color = STATION_COLORS[station_index % len(STATION_COLORS)]
            station_index += 1

        rows.append(
            {
                "name": event.name,
                "type": event.type,
                "seconds": seconds,
                "start": cursor,
                "color": color,
            }
        )
        cursor += seconds

    return rows, cursor


def _timeline_figure(rows, total):
    customdata = [
        [
            row["name"],
            format_seconds(row["seconds"]),
            f"{row['seconds'] / total * 100:.1f} %",
            f"{format_seconds(row['seconds'])} /km"
            if row["type"] == "run"
            else "atelier",
            format_seconds(row["start"] + row["seconds"]),
        ]
        for row in rows
    ]

    fig = go.Figure(
        go.Bar(
            x=[row["seconds"] for row in rows],
            base=[row["start"] for row in rows],
            y=["Épreuve"] * len(rows),
            orientation="h",
            marker={
                "color": [row["color"] for row in rows],
                "line": {"color": "white", "width": 1},
            },
            text=[SHORT_NAMES.get(row["name"], row["name"]) for row in rows],
            textposition="inside",
            insidetextanchor="middle",
            customdata=customdata,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "durée %{customdata[1]} (%{customdata[2]} du total)<br>"
                "allure %{customdata[3]}<br>"
                "cumul %{customdata[4]}<extra></extra>"
            ),
        )
    )

    for row in rows:
        center = row["start"] + row["seconds"] / 2

        fig.add_annotation(
            x=center,
            y=1.0,
            yref="paper",
            yanchor="bottom",
            text=f"{row['seconds'] / total * 100:.0f}%",
            showarrow=False,
            font={"size": 11, "color": "#334155"},
        )

        if row["type"] == "run":
            fig.add_annotation(
                x=center,
                y=0.0,
                yref="paper",
                yanchor="top",
                text=f"{format_seconds(row['seconds'])}/km",
                showarrow=False,
                font={"size": 10, "color": RUN_COLOR},
            )

    ticks = list(range(0, total + 1, 300))
    fig.update_xaxes(
        tickmode="array",
        tickvals=ticks,
        ticktext=[format_seconds(value) for value in ticks],
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.06)",
        range=[0, total],
        fixedrange=True,
    )
    fig.update_yaxes(showticklabels=False, fixedrange=True)

    fig.update_layout(
        dragmode=False,
        height=240,
        margin={"l": 20, "r": 20, "t": 30, "b": 30},
        plot_bgcolor="rgba(0, 0, 0, 0)",
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
        showlegend=False,
        bargap=0.4,
    )

    return fig


def _splits_table(rows, total):
    table_rows = [
        {
            "Épreuve": row["name"],
            "Temps": format_seconds(row["seconds"]),
            "% du total": f"{row['seconds'] / total * 100:.1f} %",
            "Allure": (
                f"{format_seconds(row['seconds'])} /km" if row["type"] == "run" else ""
            ),
        }
        for row in rows
    ]

    colors = [row["color"] for row in rows]

    def style_name(column):
        if column.name != "Épreuve":
            return [""] * len(column)

        return [f"color: {color}; font-weight: 700;" for color in colors]

    return pl.DataFrame(table_rows).to_pandas().style.apply(style_name, axis=0)


def render_team_timeline() -> None:
    team_selector("splits")

    team_name = highlighted_team()

    if not team_name:
        st.info(
            "Sélectionne une équipe ci-dessus pour afficher la décomposition "
            "de ses splits."
        )
        return

    ranking = get_ranking()
    team = next(
        (item for item in ranking.ranking if item.team == team_name),
        None,
    )

    if team is None or not team.events:
        st.info(f"Aucun split disponible pour **{team_name}**.")
        return

    events = sorted(team.events, key=lambda event: event.order)
    rows, total = _splits(events)

    st.markdown(f"#### Splits de **{team_name}**")
    st.caption(
        f"Temps total : **{team.final_time}** · course en gris, "
        "ateliers en couleur · survole un segment pour le détail."
    )

    st.plotly_chart(
        _timeline_figure(rows, total),
        width="stretch",
        config=CHART_CONFIG,
    )

    st.dataframe(
        _splits_table(rows, total),
        width="stretch",
        hide_index=True,
    )
