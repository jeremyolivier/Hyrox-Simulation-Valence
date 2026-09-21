import polars as pl
import streamlit as st

from views.charts import CHART_CONFIG, kde_by_category
from views.data import (
    category_cell_style,
    category_selector,
    get_ranking,
    highlighted_team,
    team_selector,
    zebra_style,
)

STAGE_COLUMNS = [
    "Rang",
    "Évol. générale",
    "Rang catégorie",
    "Évol. catégorie",
    "Équipe",
    "Catégorie",
    "Temps cumulé",
    "Écart",
]


def _evolution(previous_rank: int | None, current_rank: int) -> str:
    if previous_rank is None:
        return ""

    delta = previous_rank - current_rank

    if delta > 0:
        return f"▲ +{delta}"

    if delta < 0:
        return f"▼ {delta}"

    return "="


def _evolution_style(value: str) -> str:
    if isinstance(value, str) and value.startswith("▲"):
        return "color: #16A34A; font-weight: bold;"

    if isinstance(value, str) and value.startswith("▼"):
        return "color: #DC2626; font-weight: bold;"

    return ""


def _style_stage(df_pandas, highlighted: str | None):
    styler = (
        df_pandas.style
        .apply(zebra_style, axis=1)
        .map(category_cell_style, subset=["Catégorie"])
        .map(_evolution_style, subset=["Évol. générale", "Évol. catégorie"])
    )

    if highlighted:
        def highlight_row(row):
            if row.get("Équipe") == highlighted:
                return [
                    (
                        "background-color: rgba(250, 204, 21, 0.35); "
                        "font-weight: 700;"
                    )
                ] * len(row)

            return [""] * len(row)

        styler = styler.apply(highlight_row, axis=1)

    return styler


def render_stage_analysis() -> None:
    team_selector("etapes")

    ranking = get_ranking()
    labels = ranking.stage_labels()

    if not labels:
        st.info("Aucun détail d'étape disponible.")
        return

    present = [
        code for code in ("M", "F", "Mx")
        if any(team.gender == code for team in ranking.ranking)
    ]
    category = category_selector(present, key="stage_category_filter")

    # Le tableau se remplit au-dessus du slider ; la courbe se dessine dessous.
    table_slot = st.container()

    stage = st.select_slider(
        "Étape",
        options=list(range(1, len(labels) + 1)),
        value=1,
        format_func=lambda index: f"{index}. {labels[index - 1]}",
    )

    full_standings = ranking.ranking_at_stage(stage)

    previous = (
        {
            row.pid: (row.stage_rank, row.category_rank)
            for row in ranking.ranking_at_stage(stage - 1)
        }
        if stage > 1
        else {}
    )

    standings = full_standings
    if category and category != "Toutes":
        standings = [row for row in full_standings if row.gender == category]

    highlighted = highlighted_team()

    rows = []
    for row in standings:
        previous_global, previous_category = previous.get(row.pid, (None, None))
        rows.append(
            {
                "Rang": row.stage_rank,
                "Évol. générale": _evolution(previous_global, row.stage_rank),
                "Rang catégorie": row.category_rank,
                "Évol. catégorie": _evolution(
                    previous_category, row.category_rank
                ),
                "Équipe": row.team,
                "Catégorie": row.gender,
                "Temps cumulé": row.cumulative_time,
                "Écart": row.gap,
            }
        )

    styled_df = _style_stage(
        pl.DataFrame(rows).select(STAGE_COLUMNS).to_pandas(),
        highlighted,
    )

    with table_slot:
        st.markdown(
            f"#### Classement à l'issue de l'étape {stage}/{len(labels)} : "
            f"{labels[stage - 1]}"
        )
        st.caption(f"{len(standings)} équipes classées à cette étape")

        st.dataframe(
            styled_df,
            width="stretch",
            hide_index=True,
            column_config={
                "Rang": st.column_config.NumberColumn("Rang", width="small"),
                "Évol. générale": st.column_config.TextColumn(
                    "Évol. générale",
                    width="small",
                    help=(
                        "Places gagnées (▲) ou perdues (▼) au classement "
                        "général depuis l'étape précédente."
                    ),
                ),
                "Rang catégorie": st.column_config.NumberColumn(
                    "Rang catégorie",
                    width="small",
                ),
                "Évol. catégorie": st.column_config.TextColumn(
                    "Évol. catégorie",
                    width="small",
                    help=(
                        "Places gagnées (▲) ou perdues (▼) au sein de la "
                        "catégorie depuis l'étape précédente."
                    ),
                ),
                "Équipe": st.column_config.TextColumn("Équipe", width="large"),
                "Catégorie": st.column_config.TextColumn(
                    "Catégorie",
                    width="small",
                ),
                "Temps cumulé": st.column_config.TextColumn(
                    "Temps cumulé",
                    width="medium",
                ),
                "Écart": st.column_config.TextColumn("Écart", width="small"),
            },
        )

    mode = st.segmented_control(
        "Comparer sur",
        ["Temps cumulé", "Temps de l'étape"],
        default="Temps cumulé",
        key="stage_distribution_mode",
    )

    if mode == "Temps de l'étape":
        splits = ranking.stage_splits(stage)
        values_by_category = {
            code: [seconds for _, gender, seconds in splits if gender == code]
            for code in ("M", "F", "Mx")
        }
        team_split = (
            next(
                (seconds for team, _, seconds in splits if team == highlighted),
                None,
            )
            if highlighted
            else None
        )
        highlight = None
        if highlighted is not None and team_split is not None:
            highlight = (highlighted, team_split)
        heading = f"Temps sur l'étape « {labels[stage - 1]} »"
        x_title = "Temps de l'étape"
    else:
        values_by_category = {
            code: [
                row.cumulative_seconds
                for row in full_standings
                if row.gender == code
            ]
            for code in ("M", "F", "Mx")
        }
        focus = (
            next(
                (row for row in full_standings if row.team == highlighted),
                None,
            )
            if highlighted
            else None
        )
        highlight = (
            (focus.team, focus.cumulative_seconds)
            if focus is not None
            else None
        )
        heading = "Distribution des temps cumulés à cette étape"
        x_title = "Temps cumulé"

    st.markdown(f"##### {heading}")
    st.plotly_chart(
        kde_by_category(values_by_category, highlight, x_title),
        width="stretch",
        key="distribution_stage",
        config=CHART_CONFIG,
    )
