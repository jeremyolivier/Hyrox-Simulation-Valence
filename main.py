import numpy as np
import plotly.express as px
import polars as pl
import streamlit as st

from raceresult_data import get_ranking

st.set_page_config(
    page_title="Classement Hyrox Simulation Valence 2026",
    layout="wide",
)

st.title("Classement - Hyrox Simulation Valence - 20/09/2026")

st.markdown(
    """
    Application non-officielle pour visualiser quelques données sur la course
    Hyrox Simulation Valence 2026.
    """
)

st.info(
    "**Source des données :** Retrouvez le classement officiel complet sur "
    "[RaceResult](https://my.raceresult.com/405157/#0_350C18)."
)

st.divider()


@st.cache_data(ttl=300)
def load_data():
    return get_ranking()


ranking = load_data()

df = pl.DataFrame([result.model_dump() for result in ranking.ranking]).rename(
    {
        "global_rank": "Rang Général",
        "gender_rank": "Rang Catégorie",
        "pid": "ID",
        "bib": "Dossard",
        "team": "Équipe",
        "gender": "Catégorie",
        "net": "Temps Net",
        "penalty": "Pénalité",
        "final_time": "Temps Final",
        "gap": "Écart",
    }
)

VISIBLE_COLUMNS = [
    "Rang Général",
    "Rang Catégorie",
    "Dossard",
    "Équipe",
    "Catégorie",
    "Temps Final",
    "Écart",
]


# Classement
st.subheader("Classement")

col1, col2 = st.columns(2)

with col1:
    filter_column = st.selectbox(
        "Filtrer par :",
        ["Aucun filtre", "Catégorie"],
        key="ranking_filter_column",
    )

filtered_df = df

with col2:
    if filter_column != "Aucun filtre":
        unique_values = (
            df.get_column(filter_column)
            .cast(pl.String)
            .unique()
            .sort()
            .to_list()
        )

        selected_value = st.selectbox(
            f"Choisir la valeur ({filter_column}) :",
            options=["Tous"] + unique_values,
            key="ranking_selected_value",
        )

        if selected_value != "Tous":
            filtered_df = df.filter(
                pl.col(filter_column).cast(pl.String) == selected_value
            )


def style_table(df_pandas):
    def highlight_row(row):
        rank = row.get("Rang Général")

        if rank == 1:
            return [
                "background-color: rgba(255, 215, 0, 0.25); font-weight: bold;"
            ] * len(row)

        if rank == 2:
            return [
                "background-color: rgba(192, 192, 192, 0.25); font-weight: bold;"
            ] * len(row)

        if rank == 3:
            return [
                "background-color: rgba(205, 127, 50, 0.25); font-weight: bold;"
            ] * len(row)

        if row.name % 2 == 1:
            return ["background-color: rgba(240, 242, 246, 0.15);"] * len(row)

        return [""] * len(row)

    return df_pandas.style.apply(highlight_row, axis=1)


st.write(f"**{len(filtered_df)}** équipes affichées")

display_df = filtered_df.select(VISIBLE_COLUMNS)
styled_df = style_table(display_df.to_pandas())

st.dataframe(
    styled_df,
    width="stretch",
    hide_index=True,
    column_config={
        "Rang Général": st.column_config.NumberColumn(
            "Rang Général",
            width="small",
        ),
        "Rang Catégorie": st.column_config.NumberColumn(
            "Rang Catégorie",
            width="small",
        ),
        "Dossard": st.column_config.NumberColumn(
            "Dossard",
            width="small",
        ),
        "Catégorie": st.column_config.TextColumn(
            "Catégorie",
            width="small",
        ),
        "Équipe": st.column_config.TextColumn(
            "Équipe",
            width="large",
        ),
        "Temps Final": st.column_config.TextColumn(
            "Temps Final",
            width="medium",
        ),
        "Écart": st.column_config.TextColumn(
            "Écart",
            width="small",
        ),
    },
)


st.divider()
st.subheader("Distribution des temps")

col1, col2 = st.columns(2)

with col1:
    chart_filter_column = st.selectbox(
        "Filtrer par :",
        ["Aucun filtre", "Catégorie"],
        key="chart_filter_column",
    )

chart_df = df

with col2:
    if chart_filter_column != "Aucun filtre":
        unique_values = (
            df.get_column(chart_filter_column)
            .cast(pl.String)
            .unique()
            .sort()
            .to_list()
        )

        chart_selected_value = st.selectbox(
            f"Choisir la valeur ({chart_filter_column}) :",
            options=["Tous"] + unique_values,
            key="chart_selected_value",
        )

        if chart_selected_value != "Tous":
            chart_df = df.filter(
                pl.col(chart_filter_column).cast(pl.String)
                == chart_selected_value
            )


chart_df = (
    chart_df.filter(
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
        .alias("temps_secondes")
    )
)


def format_duration(seconds: int) -> str:
    hours, remainder = divmod(int(seconds), 3600)
    minutes, seconds = divmod(remainder, 60)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


BIN_COUNT = 50

times = chart_df["temps_secondes"].to_numpy()

hist, bins = np.histogram(times, bins=BIN_COUNT)


team_options = ["Aucune"] + (
    chart_df
    .select("Équipe")
    .unique()
    .sort("Équipe")
    .get_column("Équipe")
    .to_list()
)

selected_team = st.selectbox(
    "Ajouter une équipe au graphique :",
    team_options,
    key="chart_selected_team",
)


fig = px.histogram(
    chart_df,
    x="temps_secondes",
    template="plotly_white",
)

fig.update_traces(
    xbins={
        "start": bins[0],
        "end": bins[-1],
        "size": bins[1] - bins[0],
    },
    hovertemplate=(
        "Équipes : %{y}"
        "<extra></extra>"
    ),
)

mean_time = float(chart_df["temps_secondes"].mean())
median_time = float(chart_df["temps_secondes"].median())
q1 = float(chart_df["temps_secondes"].quantile(0.25))
q3 = float(chart_df["temps_secondes"].quantile(0.75))


fig.add_vline(
    x=mean_time,
    line_dash="dash",
    line_color="#E74C3C",
    annotation_text=f"Moyenne<br>{format_duration(round(mean_time))}",
    annotation_position="top",
    annotation_font={"color": "#E74C3C"},
    annotation_bgcolor="rgba(255, 255, 255, 0.9)",
    annotation_bordercolor="#E74C3C",
    annotation_borderwidth=1,
)

fig.add_vline(
    x=median_time,
    line_dash="dot",
    line_color="#3498DB",
    annotation_text=f"Médiane<br>{format_duration(round(median_time))}",
    annotation_position="bottom",
    annotation_font={"color": "#3498DB"},
    annotation_bgcolor="rgba(255, 255, 255, 0.9)",
    annotation_bordercolor="#3498DB",
    annotation_borderwidth=1,
)

fig.add_vline(
    x=q1,
    line_dash="dot",
    line_color="#7F8C8D",
    annotation_text=f"Q1<br>{format_duration(round(q1))}",
    annotation_position="top",
    annotation_font={"color": "#7F8C8D"},
    annotation_bgcolor="rgba(255, 255, 255, 0.9)",
    annotation_bordercolor="#7F8C8D",
    annotation_borderwidth=1,
)

fig.add_vline(
    x=q3,
    line_dash="dot",
    line_color="#7F8C8D",
    annotation_text=f"Q3<br>{format_duration(round(q3))}",
    annotation_position="top",
    annotation_font={"color": "#7F8C8D"},
    annotation_bgcolor="rgba(255, 255, 255, 0.9)",
    annotation_bordercolor="#7F8C8D",
    annotation_borderwidth=1,
)

if selected_team != "Aucune":
    selected_team_data = chart_df.filter(
        pl.col("Équipe") == selected_team
    ).row(0, named=True)

    selected_team_time = selected_team_data["temps_secondes"]

    fig.add_vline(
        x=selected_team_time,
        line_dash="dash",
        line_color="#8E44AD",
        annotation_text=(
            f"{selected_team}<br>"
            f"{format_duration(selected_team_time)}"
        ),
        annotation_position="top",
        annotation_font={"color": "#8E44AD"},
        annotation_bgcolor="rgba(255, 255, 255, 0.9)",
        annotation_bordercolor="#8E44AD",
        annotation_borderwidth=1,
    )


tick_values = np.linspace(
    bins[0],
    bins[-1],
    num=min(10, len(bins)),
)

fig.update_xaxes(
    tickmode="array",
    tickvals=tick_values,
    ticktext=[format_duration(value) for value in tick_values],
)

fig.update_layout(
    xaxis_title="Temps final",
    yaxis_title="Nombre d'équipes",
    bargap=0.1,
)

st.plotly_chart(fig, width="stretch")


# Informations sur l'équipe sélectionnée
if selected_team != "Aucune":
    selected_team_data = chart_df.filter(
        pl.col("Équipe") == selected_team
    ).row(0, named=True)

    selected_team_category = selected_team_data["Catégorie"]

    global_rank = selected_team_data["Rang Général"]
    category_rank = selected_team_data["Rang Catégorie"]

    global_count = len(df)

    category_count = df.filter(
        pl.col("Catégorie") == selected_team_category
    ).height

    global_percent = global_rank / global_count * 100
    category_percent = category_rank / category_count * 100

    st.markdown(
        f"**{selected_team}** est dans le **top {global_percent:.1f} %** "
        f"des équipes au classement général et dans le "
        f"**top {category_percent:.1f} %** des équipes de sa catégorie "
        f"**{selected_team_category}**."
    )


st.download_button(
    label="Exporter en CSV",
    data=filtered_df.write_csv(),
    file_name="classement_hyrox_valence_2026.csv",
    mime="text/csv",
)