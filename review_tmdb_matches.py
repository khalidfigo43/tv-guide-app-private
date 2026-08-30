import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from database import Content


DATABASE_URL = "sqlite:///data/tvguide.db"
MATCHES_FILE = Path("data/tmdb_matches.json")


def main():

    data = json.loads(
        MATCHES_FILE.read_text(
            encoding="utf-8"
        )
    )

    engine = create_engine(
        DATABASE_URL,
        echo=False,
    )

    with Session(engine) as session:

        contents = {
            str(c.id): c
            for c in session.scalars(
                select(Content)
            ).all()
        }

    # ========================================================
    # REVIEW
    # ========================================================

    print()
    print("=" * 90)
    print("TMDB MATCHES REQUIRING REVIEW")
    print("=" * 90)

    review_count = 0

    for key, item in data.items():

        if item.get("status") != "REVIEW":
            continue

        review_count += 1

        content = contents.get(key)

        print()
        print("-" * 90)

        print(
            f"Content ID : {item.get('content_id')}"
        )

        print(
            f"Source     : "
            f"{item.get('source_title')}"
        )

        print(
            f"Candidates : "
            f"{item.get('candidate_count')}"
        )

        print()

        best = item.get("best_match")

        if best:

            print("BEST MATCH")
            print(
                f"  Type          : {best.get('type')}"
            )
            print(
                f"  TMDB ID       : {best.get('tmdb_id')}"
            )
            print(
                f"  Title         : {best.get('title')}"
            )
            print(
                f"  Original      : "
                f"{best.get('original_title')}"
            )
            print(
                f"  Release Date  : "
                f"{best.get('release_date')}"
            )
            print(
                f"  Score         : "
                f"{best.get('score')}"
            )
            print(
                f"  Reasons       : "
                f"{', '.join(best.get('reasons', []))}"
            )

        second = item.get("second_match")

        if second:

            print()
            print("SECOND MATCH")
            print(
                f"  Type          : {second.get('type')}"
            )
            print(
                f"  TMDB ID       : "
                f"{second.get('tmdb_id')}"
            )
            print(
                f"  Title         : "
                f"{second.get('title')}"
            )
            print(
                f"  Original      : "
                f"{second.get('original_title')}"
            )
            print(
                f"  Release Date  : "
                f"{second.get('release_date')}"
            )
            print(
                f"  Score         : "
                f"{second.get('score')}"
            )

    # ========================================================
    # NO MATCH
    # ========================================================

    print()
    print()
    print("=" * 90)
    print("NO MATCH")
    print("=" * 90)

    no_match_count = 0

    for key, item in data.items():

        if item.get("status") != "NO_MATCH":
            continue

        no_match_count += 1

        print(
            f"{item.get('content_id'):3} | "
            f"{item.get('source_title')}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 90)
    print("REVIEW SUMMARY")
    print("=" * 90)

    print(
        f"REVIEW    : {review_count}"
    )

    print(
        f"NO_MATCH  : {no_match_count}"
    )

    print()
    print("No database changes were made.")


if __name__ == "__main__":
    main()