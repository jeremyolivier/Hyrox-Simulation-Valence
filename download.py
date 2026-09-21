"""Download results from RaceResult and write them to disk."""

from hyroxator.scraper import fetch_full_ranking
from hyroxator.storage import DATA_PATH, save_ranking


def main() -> None:
    print("Downloading ranking and details…")
    ranking = fetch_full_ranking()

    save_ranking(ranking)
    print(f"{len(ranking.ranking)} teams saved to {DATA_PATH}")


if __name__ == "__main__":
    main()
