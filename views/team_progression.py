import plotly.graph_objects as go
import streamlit as st

from views.charts import CHART_CONFIG
from views.data import get_ranking, highlighted_team, team_selector

COLORS = {
    "global": "#3B82F6",
    "category": "#F59E0B",
}


def _rank_chart(
    stages: list[int],
    global_ranks: list[int],
    category_ranks: list[int],
    stage_names: list[str],
    all_stages: list[int],
) -> go.Figure:
    fig = go.Figure()

    # Global ranking
    fig.add_trace(
        go.Scatter(
            x=stages,
            y=global_ranks,
            mode="lines+markers+text",
            line={
                "color": COLORS["global"],
                "width": 2,
            },
            marker={
                "color": COLORS["global"],
                "size": 9,
            },
            text=[str(rank) for rank in global_ranks],
            textposition="top center",
            textfont={
                "size": 11,
                "color": COLORS["global"],
            },
            customdata=stage_names,
            hovertemplate=("Étape %{x} · %{customdata}<br>Rang %{y}<extra></extra>"),
            name="Classement général",
        )
    )

    # Current global position
    fig.add_trace(
        go.Scatter(
            x=[stages[-1]],
            y=[global_ranks[-1]],
            mode="markers",
            marker={
                "color": COLORS["global"],
                "size": 16,
                "line": {
                    "color": "white",
                    "width": 2,
                },
            },
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Category ranking
    fig.add_trace(
        go.Scatter(
            x=stages,
            y=category_ranks,
            mode="lines+markers+text",
            line={
                "color": COLORS["category"],
                "width": 2,
            },
            marker={
                "color": COLORS["category"],
                "size": 9,
            },
            text=[str(rank) for rank in category_ranks],
            textposition="bottom center",
            textfont={
                "size": 11,
                "color": COLORS["category"],
            },
            customdata=stage_names,
            hovertemplate=("Étape %{x} · %{customdata}<br>Rang %{y}<extra></extra>"),
            name="Classement par catégorie",
        )
    )

    # Current category position
    fig.add_trace(
        go.Scatter(
            x=[stages[-1]],
            y=[category_ranks[-1]],
            mode="markers",
            marker={
                "color": COLORS["category"],
                "size": 16,
                "line": {
                    "color": "white",
                    "width": 2,
                },
            },
            hoverinfo="skip",
            showlegend=False,
        )
    )

    # Create one frame for each stage.
    frames = []

    for index in range(len(all_stages)):
        current_stages = all_stages[: index + 1]
        current_stage_names = stage_names[: index + 1]

        current_global_ranks = global_ranks[: index + 1]
        current_category_ranks = category_ranks[: index + 1]

        frames.append(
            go.Frame(
                name=str(all_stages[index]),
                data=[
                    go.Scatter(
                        x=current_stages,
                        y=current_global_ranks,
                        text=[str(rank) for rank in current_global_ranks],
                        customdata=current_stage_names,
                    ),
                    go.Scatter(
                        x=[current_stages[-1]],
                        y=[current_global_ranks[-1]],
                    ),
                    go.Scatter(
                        x=current_stages,
                        y=current_category_ranks,
                        text=[str(rank) for rank in current_category_ranks],
                        customdata=current_stage_names,
                    ),
                    go.Scatter(
                        x=[current_stages[-1]],
                        y=[current_category_ranks[-1]],
                    ),
                ],
            )
        )

    fig.frames = frames

    # Plotly slider
    slider_steps = []

    for index, stage in enumerate(all_stages):
        slider_steps.append(
            {
                "label": str(stage),
                "method": "animate",
                "args": [
                    [str(stage)],
                    {
                        "mode": "immediate",
                        "frame": {
                            "duration": 500,
                            "redraw": True,
                        },
                        "transition": {
                            "duration": 500,
                            "easing": "cubic-in-out",
                        },
                    },
                ],
            }
        )

    fig.update_yaxes(
        autorange="reversed",
        title="Rang",
        tickformat="d",
        showgrid=True,
        gridcolor="rgba(0, 0, 0, 0.06)",
        fixedrange=True,
    )

    fig.update_xaxes(
        title="Étape",
        range=[
            all_stages[0] - 0.5,
            all_stages[-1] + 0.5,
        ],
        tickmode="array",
        tickvals=all_stages,
        showgrid=False,
        fixedrange=True,
    )

    fig.update_layout(
        dragmode=False,
        height=420,
        margin={
            "l": 20,
            "r": 20,
            "t": 60,
            "b": 80,
        },
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
        showlegend=True,
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "center",
            "x": 0.5,
        },
        sliders=[
            {
                "active": len(all_stages) - 1,
                "currentvalue": {
                    "prefix": "Étape : ",
                },
                "pad": {
                    "t": 20,
                },
                "steps": slider_steps,
            }
        ],
    )

    return fig


def render_team_progression() -> None:
    team_selector("progression")

    team_name = highlighted_team()

    if not team_name:
        st.info(
            "Sélectionne une équipe ci-dessus pour voir son évolution au classement."
        )
        return

    ranking = get_ranking()

    team = next(
        (item for item in ranking.ranking if item.team == team_name),
        None,
    )

    if team is None:
        st.info(f"Aucune donnée pour **{team_name}**.")
        return

    labels = ranking.stage_labels()
    progression = ranking.team_progression(team.pid)

    if not progression:
        st.info(f"**{team_name}** n'a pas de classement par étape (splits incomplets).")
        return

    all_stages = [item[0] for item in progression]

    stage_names = [labels[item[0] - 1] for item in progression]

    global_ranks = [item[1] for item in progression]

    category_ranks = [item[2] for item in progression]

    # Start by displaying the complete race.
    stages = all_stages
    displayed_stage_names = stage_names

    st.markdown("##### Classement")

    fig = _rank_chart(
        stages=stages,
        global_ranks=global_ranks,
        category_ranks=category_ranks,
        stage_names=displayed_stage_names,
        all_stages=all_stages,
    )

    st.plotly_chart(
        fig,
        width="stretch",
        config=CHART_CONFIG,
    )
