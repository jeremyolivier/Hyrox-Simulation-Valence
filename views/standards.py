import polars as pl
import streamlit as st

from views.data import CATEGORY_COLORS, hex_to_rgba

STATIONS = [
    ("SkiErg", "1 000 m", "", "", ""),
    ("Sled Push", "50 m", "152 kg", "102 kg", "152 kg"),
    ("Sled Pull", "50 m", "103 kg", "78 kg", "103 kg"),
    (
        "Burpee Broad Jumps",
        "80 m",
        "Poids du corps",
        "Poids du corps",
        "Poids du corps",
    ),
    ("Rowing", "1 000 m", "", "", ""),
    ("Farmers Carry", "200 m", "2 × 24 kg", "2 × 16 kg", "2 × 24 kg"),
    ("Sandbag Lunges", "100 m", "20 kg", "10 kg", "20 kg"),
    ("Wall Balls", "100 reps", "6 kg · 3,0 m", "4 kg · 2,7 m", "6 kg · 3,0 m"),
]

COLUMN_TO_CODE = {"Hommes": "M", "Femmes": "F", "Mixte": "Mx"}

STATION_COLORS = [
    "#0EA5E9",
    "#EF4444",
    "#F97316",
    "#8B5CF6",
    "#06B6D4",
    "#10B981",
    "#CA8A04",
    "#DB2777",
]


def _style_standards(df_pandas):
    def column_style(column):
        if column.name == "Atelier":
            return [
                f"background-color: {hex_to_rgba(color, 0.12)}; "
                f"color: {color}; font-weight: 700;"
                for color in STATION_COLORS
            ]

        category_color = CATEGORY_COLORS.get(COLUMN_TO_CODE.get(column.name))

        if not category_color:
            return [""] * len(column)

        return [f"background-color: {hex_to_rgba(category_color, 0.14)};"] * len(column)

    return df_pandas.style.apply(column_style, axis=0)


def render_standards() -> None:
    st.markdown(
        "Le déroulé : **8 tours**, chacun composé d'un **1 000 m de course** "
        "suivi d'un atelier, dans l'ordre ci-dessous. Charges de la division "
        "**Open** (en doubles, le mixte utilise les charges hommes)."
    )

    df = pl.DataFrame(
        STATIONS,
        schema=["Atelier", "Distance / Reps", "Hommes", "Femmes", "Mixte"],
        orient="row",
    )

    st.dataframe(
        _style_standards(df.to_pandas()),
        width="stretch",
        hide_index=True,
        column_config={
            "Atelier": st.column_config.TextColumn("Atelier", width="medium"),
            "Distance / Reps": st.column_config.TextColumn(
                "Distance / Reps",
                width="small",
            ),
            "Hommes": st.column_config.TextColumn("Hommes", width="small"),
            "Femmes": st.column_config.TextColumn("Femmes", width="small"),
            "Mixte": st.column_config.TextColumn("Mixte", width="small"),
        },
    )

    st.caption(
        "Charges de la division Open · Source officielle : "
        "[HYROX](https://hyrox.com/the-fitness-race/)."
    )
