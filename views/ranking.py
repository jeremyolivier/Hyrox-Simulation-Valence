import polars as pl
import streamlit as st

from views.data import VISIBLE_COLUMNS, get_dataframe


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


@st.fragment
def render_ranking() -> None:
    df = get_dataframe()

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

    st.download_button(
        label="Exporter en CSV",
        data=filtered_df.write_csv(),
        file_name="classement_hyrox_valence_2026.csv",
        mime="text/csv",
    )
