import asyncio
import re
from typing import Literal

import httpx2
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


def _clean_str(val: str) -> str:
    """Remove HTML tags and extra whitespace."""
    if not isinstance(val, str):
        return ""

    clean = re.sub(r"<[^>]*>", "", val)
    return clean.strip()


class RunResult(BaseModel):
    number: int
    time: str


class StationResult(BaseModel):
    number: int
    name: str
    time: str


class EventResult(BaseModel):
    order: int
    type: Literal["run", "station"]
    name: str
    time: str


class TeamResult(BaseModel):
    pid: int
    team: str
    global_rank: int
    gender_rank: int
    bib: int
    gender: Literal["M", "F", "Mx"]
    net: str
    penalty: str
    final_time: str
    gap: str

    runs: list[RunResult] = Field(default_factory=list)
    stations: list[StationResult] = Field(default_factory=list)
    events: list[EventResult] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def parse_row(cls, row: list[str]) -> dict:
        cleaned_row = [_clean_str(cell) for cell in row]

        raw_category = cleaned_row[5] if len(cleaned_row) > 5 else ""

        gender_rank_match = re.search(r"\((\d+)\)", raw_category)
        gender_rank = int(gender_rank_match.group(1)) if gender_rank_match else 0

        global_rank_str = cleaned_row[2].rstrip(".") if len(cleaned_row) > 2 else "0"
        global_rank = int(global_rank_str) if global_rank_str.isdigit() else 0

        bib_str = cleaned_row[3] if len(cleaned_row) > 3 else "0"
        bib = int(bib_str) if bib_str.isdigit() else 0

        pid_str = cleaned_row[1] if len(cleaned_row) > 1 else "0"
        pid = int(pid_str) if pid_str.isdigit() else 0

        return {
            "global_rank": global_rank,
            "gender_rank": gender_rank,
            "pid": pid,
            "bib": bib,
            "team": cleaned_row[4] if len(cleaned_row) > 4 else "",
            "gender": raw_category.split(" ")[0] if raw_category else "M",
            "net": cleaned_row[6] if len(cleaned_row) > 6 else "",
            "penalty": cleaned_row[7] if len(cleaned_row) > 7 else "",
            "final_time": cleaned_row[8] if len(cleaned_row) > 8 else "",
            "gap": cleaned_row[9] if len(cleaned_row) > 9 else "",
        }


class TeamsRanking(BaseModel):
    ranking: list[TeamResult]

    @field_validator("ranking", mode="before")
    @classmethod
    def filter_invalid_teams(cls, raw_list: list) -> list[TeamResult]:
        valid_items = []
        errors_count = 0

        for item in raw_list:
            try:
                if isinstance(item, TeamResult):
                    valid_items.append(item)
                else:
                    valid_items.append(TeamResult.model_validate(item))
            except (
                    ValidationError,
                    IndexError,
                    KeyError,
                    TypeError,
                    ValueError,
            ) as e:
                errors_count += 1
                print(
                    f"[DEBUG Pydantic] Validation failed: {e} | "
                    f"Item: {item}"
                )

        print(
            f"\n[DEBUG Pydantic] Valid teams: {len(valid_items)} / "
            f"Ignored: {errors_count}"
        )

        return valid_items

    def by_gender(
            self,
            gender: Literal["M", "F", "Mx"],
            sort: bool = True,
    ) -> list[TeamResult]:
        filtered = [
            team for team in self.ranking
            if team.gender == gender
        ]

        if sort:
            return sorted(
                filtered,
                key=lambda team: team.gender_rank,
            )

        return filtered

    def by_global_rank(self) -> list[TeamResult]:
        return sorted(
            self.ranking,
            key=lambda team: team.global_rank,
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


ranking = get_ranking()

asyncio.run(load_details(ranking))

print(ranking)