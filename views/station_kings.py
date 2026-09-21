import streamlit as st

from views.data import category_selector, format_seconds, get_ranking

SHORT = {"Burpee Broad Jumps": "BBJ"}


def render_station_kings() -> None:
    ranking = get_ranking()

    reference = max(
        ranking.ranking,
        key=lambda team: len(team.events),
        default=None,
    )

    if reference is None or not reference.events:
        st.info("Aucun détail d'atelier disponible.")
        return

    stations = [
        (event.name, event.order)
        for event in sorted(reference.events, key=lambda item: item.order)
        if event.type == "station"
    ]

    present = [
        code
        for code in ("M", "F", "Mx")
        if any(team.gender == code for team in ranking.ranking)
    ]
    category = category_selector(present, key="kings_category_filter")

    st.caption("Les meilleurs temps sur chaque atelier.")

    for start in range(0, len(stations), 4):
        columns = st.columns(4)

        for column, (name, order) in zip(columns, stations[start : start + 4]):
            splits = ranking.stage_splits(order)

            if category and category != "Toutes":
                splits = [row for row in splits if row[1] == category]

            splits.sort(key=lambda row: row[2])

            with column.container(border=True):
                st.markdown(f"**{SHORT.get(name, name)}**")

                if not splits:
                    st.markdown("Aucun temps")
                    continue

                king_team, _, king_seconds = splits[0]
                st.markdown(f"### {format_seconds(king_seconds)}")
                st.markdown(f"🥇 {king_team}")

                extra = []
                if len(splits) > 1:
                    team, _, seconds = splits[1]
                    extra.append(f"🥈 {format_seconds(seconds)} · {team}")
                if len(splits) > 2:
                    team, _, seconds = splits[2]
                    extra.append(f"🥉 {format_seconds(seconds)} · {team}")

                if extra:
                    st.markdown("  \n".join(extra))
