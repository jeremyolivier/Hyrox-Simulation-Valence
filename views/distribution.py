import numpy as np
import polars as pl
import streamlit as st

from views.charts import CHART_CONFIG, kde_by_category
from views.data import (
    CATEGORY_COLORS,
    CATEGORY_LABELS,
    get_dataframe,
    highlighted_team,
    team_selector,
)

CATEGORIES = {
    code: (CATEGORY_LABELS[code], CATEGORY_COLORS[code])
    for code in CATEGORY_LABELS
}


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def render_distribution() -> None:
    team_selector("distribution")

    df = get_dataframe()

    parsed_df = (
        df.filter(
            pl.col("Temps Final").is_not_null() & (pl.col("Temps Final") != "")
        )
        .with_columns(
            pl.col("Temps Final").str.split(":").alias("time_parts")
        )
        .with_columns(
            pl.when(pl.col("time_parts").list.len() == 2)
            .then(
                pl.col("time_parts").list.get(0).cast(pl.Int64) * 60
                + pl.col("time_parts").list.get(1).cast(pl.Int64)
            )
            .when(pl.col("time_parts").list.len() == 3)
            .then(
                pl.col("time_parts").list.get(0).cast(pl.Int64) * 3600
                + pl.col("time_parts").list.get(1).cast(pl.Int64) * 60
                + pl.col("time_parts").list.get(2).cast(pl.Int64)
            )
            .alias("total_seconds")
        )
        .filter(pl.col("total_seconds").is_not_null())
    )

    present_cats = set(parsed_df.get_column("Catégorie").unique().to_list())
    selected_cats = [code for code in CATEGORIES if code in present_cats]

    subset = parsed_df

    stats_rows = [
        {
            "Catégorie": CATEGORIES[cat][0],
            "Équipes": len(values),
            "Meilleur": format_duration(int(values.min())),
            "Moyenne": format_duration(round(float(values.mean()))),
            "Médiane": format_duration(round(float(np.median(values)))),
        }
        for cat in selected_cats
        for values in [
            subset.filter(pl.col("Catégorie") == cat)["total_seconds"].to_numpy()
        ]
    ]

    st.dataframe(
        pl.DataFrame(stats_rows),
        hide_index=True,
        width="stretch",
    )

    selected_team = highlighted_team()
    team_in_subset = (
        selected_team is not None
        and subset.filter(pl.col("Équipe") == selected_team).height > 0
    )

    values_by_category = {
        cat: subset.filter(pl.col("Catégorie") == cat)["total_seconds"].to_numpy()
        for cat in selected_cats
    }

    highlight = None
    if team_in_subset:
        selected_team_time = subset.filter(
            pl.col("Équipe") == selected_team
        ).row(0, named=True)["total_seconds"]
        highlight = (selected_team, selected_team_time)

    st.plotly_chart(
        kde_by_category(values_by_category, highlight, "Temps final"),
        width="stretch",
        key="distribution_general",
        config=CHART_CONFIG,
    )

    if team_in_subset:
        team_row = subset.filter(
            pl.col("Équipe") == selected_team
        ).row(0, named=True)

        team_category = team_row["Catégorie"]

        global_rank = team_row["Rang Général"]
        global_total = len(df)
        global_percent = global_rank / global_total * 100

        category_rank = team_row["Rang Catégorie"]
        category_total = df.filter(pl.col("Catégorie") == team_category).height
        category_percent = category_rank / category_total * 100

        st.markdown(
            f"**{selected_team}** est **{global_rank}/{global_total}** "
            f"(top {global_percent:.1f} %) au classement général et "
            f"**{category_rank}/{category_total}** "
            f"(top {category_percent:.1f} %) dans sa catégorie "
            f"**{team_category}**."
        )
