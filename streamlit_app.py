import streamlit as st

from views.distribution import render_distribution
from views.ranking import render_ranking

st.set_page_config(
    page_title="Classement Hyrox Simulation Valence 2026",
    page_icon="🏃",
    layout="wide",
)

SECTIONS = [
    (":material/leaderboard:", "Classement", "classement", render_ranking),
    (
        ":material/bar_chart:",
        "Distribution des temps",
        "distribution-des-temps",
        render_distribution,
    ),
]

with st.sidebar:
    st.markdown("### Sections")
    for icon, title, anchor, _ in SECTIONS:
        st.markdown(f"[{icon} {title}](#{anchor})")

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

for icon, title, anchor, render in SECTIONS:
    st.divider()
    st.subheader(f"{icon} {title}", anchor=anchor)
    render()
