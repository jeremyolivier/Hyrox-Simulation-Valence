from pathlib import Path

from hyroxator.models import TeamsRanking

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "results.json"


def save_ranking(ranking: TeamsRanking, path: Path = DATA_PATH) -> None:
    """Save the ranking to disk as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        ranking.model_dump_json(indent=2),
        encoding="utf-8",
    )


def load_ranking(path: Path = DATA_PATH) -> TeamsRanking:
    """Load the ranking from disk (no network call)."""
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}\nRun the download first: python download.py"
        )

    return TeamsRanking.model_validate_json(
        path.read_text(encoding="utf-8"),
    )
