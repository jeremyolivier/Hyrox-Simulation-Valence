import re
from typing import Literal

from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator


def _clean_str(val: str) -> str:
    if not isinstance(val, str):
        return ""

    clean = re.sub(r"<[^>]*>", "", val)
    return clean.strip()


def _time_to_seconds(value: str) -> int | None:
    parts = value.split(":")

    if not value or not all(part.isdigit() for part in parts):
        return None

    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])

    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

    return None


def _format_seconds(total: int) -> str:
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    return f"{minutes:02d}:{seconds:02d}"


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
    def parse_row(cls, row: list[str] | dict) -> dict:
        if isinstance(row, dict):
            return row

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


class StageStanding(BaseModel):
    stage_rank: int
    category_rank: int
    pid: int
    bib: int
    team: str
    gender: Literal["M", "F", "Mx"]
    cumulative_seconds: int
    cumulative_time: str
    gap: str


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
                print(f"[DEBUG Pydantic] Validation failed: {e} | Item: {item}")

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
        filtered = [team for team in self.ranking if team.gender == gender]

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

    def stage_splits(self, stage: int) -> list[tuple[str, str, int]]:
        splits = []

        for team in self.ranking:
            event = next(
                (item for item in team.events if item.order == stage),
                None,
            )

            if event is None:
                continue

            seconds = _time_to_seconds(event.time)

            if seconds is None:
                continue

            splits.append((team.team, team.gender, seconds))

        return splits

    def team_progression(self, pid: int) -> list[tuple[int, int, int]]:
        progression: list[tuple[int, int, int]] = []

        for stage in range(1, len(self.stage_labels()) + 1):
            for row in self.ranking_at_stage(stage):
                if row.pid == pid:
                    progression.append((stage, row.stage_rank, row.category_rank))
                    break

        return progression

    def stage_labels(self) -> list[str]:
        reference = max(
            self.ranking,
            key=lambda team: len(team.events),
            default=None,
        )

        if reference is None:
            return []

        return [event.name for event in sorted(reference.events, key=lambda e: e.order)]

    def ranking_at_stage(self, stage: int) -> list[StageStanding]:
        cumulated: list[tuple[TeamResult, int]] = []

        for team in self.ranking:
            events = [event for event in team.events if event.order <= stage]

            if len(events) < stage:
                continue

            seconds = [_time_to_seconds(event.time) for event in events]

            if any(value is None for value in seconds):
                continue

            cumulated.append(
                (team, sum(value for value in seconds if value is not None))
            )

        cumulated.sort(key=lambda item: item[1])

        if not cumulated:
            return []

        leader_seconds = cumulated[0][1]
        category_counts: dict[str, int] = {}
        standings: list[StageStanding] = []

        for index, (team, total) in enumerate(cumulated):
            category_counts[team.gender] = category_counts.get(team.gender, 0) + 1
            gap = total - leader_seconds

            standings.append(
                StageStanding(
                    stage_rank=index + 1,
                    category_rank=category_counts[team.gender],
                    pid=team.pid,
                    bib=team.bib,
                    team=team.team,
                    gender=team.gender,
                    cumulative_seconds=total,
                    cumulative_time=_format_seconds(total),
                    gap="" if gap == 0 else f"+{_format_seconds(gap)}",
                )
            )

        return standings
