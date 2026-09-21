import numpy as np
import plotly.graph_objects as go
import polars as pl
import streamlit as st
from scipy.stats import gaussian_kde

from views.data import get_dataframe

CATEGORIES = {
    "M": ("Hommes (M)", "#3B82F6"),
    "F": ("Femmes (F)", "#EC4899"),
    "Mx": ("Mixte (Mx)", "#F59E0B"),
}


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    red, green, blue = (int(h[i:i + 2], 16) for i in (0, 2, 4))

    return f"rgba({red}, {green}, {blue}, {alpha})"


@st.fragment
def render_distribution() -> None:
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

    st.caption(
        "Clique une catégorie dans la légende pour la masquer ou l'afficher."
    )

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

    team_options = ["Aucune"] + (
        subset
        .select("Équipe")
        .unique()
        .sort("Équipe")
        .get_column("Équipe")
        .to_list()
    )

    selected_team = st.selectbox(
        "Mettre une équipe en évidence :",
        team_options,
        key="chart_selected_team",
    )

    plottable = [
        cat
        for cat in selected_cats
        for series in [
            subset.filter(pl.col("Catégorie") == cat)["total_seconds"]
        ]
        if series.len() >= 2 and series.n_unique() > 1
    ]

    all_times = subset["total_seconds"].to_numpy()
    x_grid = np.linspace(all_times.min(), all_times.max(), 200)
    x_labels = [format_duration(value) for value in x_grid]

    fig = go.Figure()

    densities = []

    for cat in plottable:
        data = subset.filter(
            pl.col("Catégorie") == cat
        )["total_seconds"].to_numpy()

        density = gaussian_kde(data)(x_grid)
        densities.append(density)

        label, color = CATEGORIES[cat]

        fig.add_scatter(
            x=x_grid,
            y=density,
            name=label,
            mode="lines",
            line={"color": color, "width": 2},
            fill="tozeroy",
            fillcolor=hex_to_rgba(color, 0.18),
            customdata=x_labels,
            hovertemplate=f"<b>{label}</b><br>%{{customdata}}<extra></extra>",
        )

    max_density = max((density.max() for density in densities), default=1.0)
    rug_step = max_density * 0.06

    for index, cat in enumerate(plottable):
        data = subset.filter(
            pl.col("Catégorie") == cat
        )["total_seconds"].to_numpy()

        _, color = CATEGORIES[cat]

        fig.add_scatter(
            x=data,
            y=np.full(len(data), -rug_step * (index + 1)),
            mode="markers",
            marker={"symbol": "line-ns-open", "color": color, "size": 8},
            showlegend=False,
            hoverinfo="skip",
        )

    if selected_team != "Aucune":
        selected_team_time = subset.filter(
            pl.col("Équipe") == selected_team
        ).row(0, named=True)["total_seconds"]

        fig.add_vline(
            x=selected_team_time,
            line_color="#7C3AED",
            line_width=2.5,
            annotation_text=(
                f"{selected_team} · {format_duration(selected_team_time)}"
            ),
            annotation_position="top left",
            annotation_font={"color": "#7C3AED", "size": 12},
        )

    tick_values = np.linspace(all_times.min(), all_times.max(), num=8)

    fig.update_xaxes(
        tickmode="array",
        tickvals=tick_values,
        ticktext=[format_duration(value) for value in tick_values],
        showgrid=False,
        ticks="outside",
        tickcolor="rgba(0, 0, 0, 0.15)",
    )

    fig.update_yaxes(
        showticklabels=False,
        showgrid=False,
        zeroline=True,
        zerolinecolor="rgba(0, 0, 0, 0.15)",
        range=[-rug_step * (len(plottable) + 1), max_density * 1.12],
    )

    fig.update_layout(
        xaxis_title="Temps final",
        yaxis_title="Densité d'équipes",
        height=480,
        margin={"l": 20, "r": 20, "t": 60, "b": 20},
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
        legend={
            "title": "Catégorie",
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
    )

    st.plotly_chart(fig, width="stretch")

    if selected_team != "Aucune":
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
