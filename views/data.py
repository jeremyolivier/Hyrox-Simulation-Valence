import polars as pl
import streamlit as st

from hyroxator import load_ranking

VISIBLE_COLUMNS = [
    "Rang Général",
    "Rang Catégorie",
    "Dossard",
    "Équipe",
    "Catégorie",
    "Temps Final",
    "Écart",
]


@st.cache_data
def get_dataframe() -> pl.DataFrame:
    """Load the ranking from disk and return it as a renamed DataFrame."""
    ranking = load_ranking()

    rows = [
        result.model_dump(exclude={"runs", "stations", "events"})
        for result in ranking.ranking
    ]

    return pl.DataFrame(rows).rename(
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
