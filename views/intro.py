import streamlit as st

from views.data import gender_breakdown


def render_intro() -> None:
    st.title("HYROX Simulation Valence 2026")
    st.markdown("**Course en doubles** · Valence · 20 septembre 2026")

    counts = gender_breakdown()
    total = sum(counts.values())
    men = 2 * counts["M"] + counts["Mx"]
    women = 2 * counts["F"] + counts["Mx"]

    with st.container(border=True):
        columns = st.columns(4)
        columns[0].metric("Duos classés", total)
        columns[1].metric("Hommes (M)", counts["M"])
        columns[2].metric("Femmes (F)", counts["F"])
        columns[3].metric("Mixtes (Mx)", counts["Mx"])

    st.markdown(
        f"{men + women} participants ({men} hommes, {women} femmes) · "
        "données non-officielles, source "
        "[RaceResult](https://my.raceresult.com/405157/#0_350C18)"
    )
