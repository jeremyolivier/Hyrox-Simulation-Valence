import asyncio
import re

import httpx2

from hyroxator.models import (
    EventResult,
    RunResult,
    StationResult,
    TeamsRanking,
)


def get_ranking() -> TeamsRanking:
    url = (
        "https://my4.raceresult.com/405157/results/list"
        "?key=ff3dbf9009144568664f1b870c671a3c"
        "&listname=02-Classements%7CClassement+g%C3%A9n%C3%A9ral"
        "&page=results"
        "&contest=0"
        "&r=all"
        "&l=0"
        "&openedGroups=%7B%7D"
        "&term="
    )

    response = httpx2.get(url)
    response.raise_for_status()

    data = response.json().get("data", [])

    if isinstance(data, dict):
        raw_rows = []

        for rows in data.values():
            if isinstance(rows, list):
                raw_rows.extend(rows)
    else:
        raw_rows = data

    return TeamsRanking(ranking=raw_rows)


def _get_run_result(pid: int) -> list[RunResult]:
    url = (
        "https://my4.raceresult.com/405157/partresulthyrox/list"
        "?key=ff3dbf9009144568664f1b870c671a3c"
        "&listname=02-Classements|99-Runs_détails"
        "&page=partresulthyrox"
        f"&r=pid&pid={pid}"
    )

    response = httpx2.get(url)
    response.raise_for_status()

    data = response.json().get("data", [])

    return [
        RunResult(
            number=index + 1,
            time=row[3],
        )
        for index, row in enumerate(data)
        if len(row) >= 4
    ]


def _get_station_result(pid: int) -> list[StationResult]:
    url = (
        "https://my4.raceresult.com/405157/partresulthyrox/list"
        "?key=ff3dbf9009144568664f1b870c671a3c"
        "&listname=02-Classements|99-Ateliers_détails"
        "&page=partresulthyrox"
        f"&r=pid&pid={pid}"
    )

    response = httpx2.get(url)
    response.raise_for_status()

    data = response.json().get("data", [])

    return [
        StationResult(
            number=index + 1,
            name=re.sub(r"^\s*\d+\s*-\s*", "", row[2]),
            time=row[3],
        )
        for index, row in enumerate(data)
        if len(row) >= 4
    ]


async def get_run_result(pid: int) -> list[RunResult]:
    return await asyncio.to_thread(_get_run_result, pid)


async def get_station_result(pid: int) -> list[StationResult]:
    return await asyncio.to_thread(_get_station_result, pid)


def build_events(
        runs: list[RunResult],
        stations: list[StationResult],
) -> list[EventResult]:
    events = []

    runs_by_number = {run.number: run for run in runs}
    stations_by_number = {
        station.number: station
        for station in stations
    }

    for number in range(1, 9):
        run = runs_by_number.get(number)
        if run:
            events.append(
                EventResult(
                    order=len(events) + 1,
                    type="run",
                    name=f"Run {run.number}",
                    time=run.time,
                )
            )

        station = stations_by_number.get(number)
        if station:
            events.append(
                EventResult(
                    order=len(events) + 1,
                    type="station",
                    name=station.name,
                    time=station.time,
                )
            )

    return events


async def load_details(ranking: TeamsRanking) -> None:
    results = await asyncio.gather(
        *(
            asyncio.gather(
                get_run_result(team.pid),
                get_station_result(team.pid),
            )
            for team in ranking.ranking
        )
    )

    for team, (runs, stations) in zip(ranking.ranking, results):
        team.runs = runs
        team.stations = stations
        team.events = build_events(runs, stations)


def fetch_full_ranking() -> TeamsRanking:
    """Download the ranking and per-team details from RaceResult."""
    ranking = get_ranking()
    asyncio.run(load_details(ranking))
    return ranking
