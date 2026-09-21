import polars as pl
import streamlit as st

from hyroxator import TeamsRanking, load_ranking

VISIBLE_COLUMNS = [
    "Rang Général",
    "Rang Catégorie",
    "Équipe",
    "Catégorie",
    "Temps Final",
    "Écart",
]

CATEGORY_LABELS = {
    "M": "Hommes (M)",
    "F": "Femmes (F)",
    "Mx": "Mixte (Mx)",
}

CATEGORY_COLORS = {
    "M": "#3B82F6",
    "F": "#EC4899",
    "Mx": "#F59E0B",
}


def hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    red, green, blue = (int(h[i:i + 2], 16) for i in (0, 2, 4))

    return f"rgba({red}, {green}, {blue}, {alpha})"


def category_cell_style(category: str) -> str:
    color = CATEGORY_COLORS.get(category)

    if not color:
        return ""

    return f"background-color: {hex_to_rgba(color, 0.22)}; font-weight: 600;"


def zebra_style(row):
    if row.name % 2:
        return ["background-color: rgba(128, 128, 128, 0.08);"] * len(row)

    return [""] * len(row)


def category_selector(present: list[str], key: str) -> str | None:
    return st.segmented_control(
        "Catégorie",
        ["Toutes", *present],
        default="Toutes",
        key=key,
    )


@st.cache_data
def get_ranking() -> TeamsRanking:
    """Load the ranking model from disk (teams with a final time only)."""
    ranking = load_ranking()
    ranking.ranking = [team for team in ranking.ranking if team.final_time]

    return ranking


@st.cache_data
def get_dataframe() -> pl.DataFrame:
    """Load the ranking from disk and return it as a renamed DataFrame."""
    ranking = load_ranking()

    rows = [
        result.model_dump(exclude={"runs", "stations", "events"})
        for result in ranking.ranking
        if result.final_time
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


def gender_breakdown() -> dict[str, int]:
    column = get_dataframe().get_column("Catégorie")

    return {code: int((column == code).sum()) for code in ("M", "F", "Mx")}


def team_names() -> list[str]:
    return (
        get_dataframe()
        .get_column("Équipe")
        .unique()
        .sort()
        .to_list()
    )


def highlighted_team() -> str | None:
    team = st.session_state.get("team")

    return None if not team or team == "Aucune" else team


def _sync_team(key: str) -> None:
    st.session_state["team"] = st.session_state[key]


def team_selector(suffix: str) -> None:
    options = ["Aucune", *team_names()]
    canonical = st.session_state.get("team", "Aucune")

    if canonical not in options:
        canonical = "Aucune"

    key = f"team_selector_{suffix}"
    st.session_state[key] = canonical

    st.selectbox(
        "Équipe à mettre en avant sur toute l'analyse",
        options,
        key=key,
        on_change=_sync_team,
        args=(key,),
    )


def format_seconds(total: int) -> str:
    hours, remainder = divmod(int(total), 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"
