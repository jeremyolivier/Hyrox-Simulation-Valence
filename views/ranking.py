import polars as pl
import streamlit as st

from views.data import (
    VISIBLE_COLUMNS,
    category_cell_style,
    category_selector,
    get_dataframe,
    highlighted_team,
    team_selector,
    zebra_style,
)


def style_table(df_pandas):
    return (
        df_pandas.style
        .apply(zebra_style, axis=1)
        .map(category_cell_style, subset=["Catégorie"])
    )


def _column_config():
    return {
        "Rang Général": st.column_config.NumberColumn("Rang Général", width="small"),
        "Rang Catégorie": st.column_config.NumberColumn(
            "Rang Catégorie",
            width="small",
        ),
        "Catégorie": st.column_config.TextColumn("Catégorie", width="small"),
        "Équipe": st.column_config.TextColumn("Équipe", width="large"),
        "Temps Final": st.column_config.TextColumn("Temps Final", width="medium"),
        "Écart": st.column_config.TextColumn("Écart", width="small"),
    }


def render_ranking() -> None:
    team_selector("classement")

    df = get_dataframe()

    present = [
        code for code in ("M", "F", "Mx")
        if (df.get_column("Catégorie") == code).any()
    ]
    category = category_selector(present, key="ranking_category_filter")

    filtered_df = df
    if category and category != "Toutes":
        filtered_df = df.filter(pl.col("Catégorie") == category)

    st.write(f"**{len(filtered_df)}** équipes affichées")

    st.dataframe(
        style_table(filtered_df.select(VISIBLE_COLUMNS).to_pandas()),
        width="stretch",
        hide_index=True,
        column_config=_column_config(),
    )

    highlighted = highlighted_team()
    if highlighted:
        focus = df.filter(pl.col("Équipe") == highlighted).select(VISIBLE_COLUMNS)

        if focus.height:
            st.markdown(f"**Équipe mise en avant : {highlighted}**")
            st.dataframe(
                style_table(focus.to_pandas()),
                width="stretch",
                hide_index=True,
                column_config=_column_config(),
            )
        else:
            st.caption(f"{highlighted} n'apparaît pas dans ce classement.")

    st.download_button(
        label="Exporter en CSV",
        data=filtered_df.write_csv(),
        file_name="classement_hyrox_valence_2026.csv",
        mime="text/csv",
    )
