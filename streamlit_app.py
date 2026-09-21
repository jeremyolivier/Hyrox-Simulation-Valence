import streamlit as st

from views.data import restore_team_from_url
from views.distribution import render_distribution
from views.intro import render_intro
from views.ranking import render_ranking
from views.stage_analysis import render_stage_analysis
from views.standards import render_standards
from views.station_kings import render_station_kings
from views.team_progression import render_team_progression
from views.team_radar import render_team_radar
from views.team_timeline import render_team_timeline

st.set_page_config(
    page_title="Classement Hyrox Simulation Valence 2026",
    page_icon="🏃",
    layout="wide",
)

GROUPS = [
    (
        "Le format",
        [
            (
                ":material/fitness_center:",
                "Déroulé d'un Hyrox - Open",
                "deroule",
                render_standards,
            ),
        ],
    ),
    (
        "Analyse générale",
        [
            (
                ":material/leaderboard:",
                "Classement",
                "classement",
                render_ranking,
            ),
            (
                ":material/bar_chart:",
                "Distribution des temps",
                "distribution",
                render_distribution,
            ),
        ],
    ),
    (
        "Analyse par étapes",
        [
            (
                ":material/trending_up:",
                "Classement & distribution par étape",
                "par-etapes",
                render_stage_analysis,
            ),
        ],
    ),
    (
        "Focus équipe",
        [
            (
                ":material/show_chart:",
                "Évolution au classement",
                "evolution-classement",
                render_team_progression,
            ),
            (
                ":material/radar:",
                "Profil de l'équipe",
                "profil-equipe",
                render_team_radar,
            ),
            (
                ":material/timeline:",
                "Splits de l'équipe",
                "splits-equipe",
                render_team_timeline,
            ),
        ],
    ),
    (
        "Les meilleurs par épreuve",
        [
            (
                ":material/show_chart:",
                "Meilleurs par épreuve",
                "meilleurs-par-station",
                render_station_kings,
            ),
        ],
    ),
]
with st.sidebar:
    for group_name, sections in GROUPS:
        st.markdown(f"**{group_name}**")
        for icon, title, anchor, _ in sections:
            st.markdown(f"[{icon} {title}](#{anchor})")

restore_team_from_url()

render_intro()

for group_name, sections in GROUPS:
    st.divider()
    st.header(group_name)
    for _icon, title, anchor, render in sections:
        st.subheader(title, anchor=anchor)
        render()
