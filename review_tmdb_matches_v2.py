import json
from pathlib import Path

MATCHES_FILE = Path("data/tmdb_matches_v2.json")


def main():

    data = json.loads(
        MATCHES_FILE.read_text(
            encoding="utf-8"
        )
    )

    print("=" * 90)
    print("TMDB V2 REVIEW")
    print("=" * 90)

    review_count = 0

    for item in data.values():

        if item.get("status") != "REVIEW":
            continue

        review_count += 1

        print()
        print("-" * 90)

        print(
            f"Content ID : {item['content_id']}"
        )

        print(
            f"Source     : {item['source_title']}"
        )

        print(
            f"Channels   : "
            f"{', '.join(item.get('channels', []))}"
        )

        print(
            f"Channel hint: "
            f"{item.get('channel_hint')}"
        )

        print()

        candidates = item.get(
            "candidates",
            []
        )

        for index, candidate in enumerate(
            candidates[:5],
            start=1,
        ):

            print(
                f"{index}. "
                f"[{candidate['type']}] "
                f"{candidate['title']}"
            )

            print(
                f"   TMDB ID   : "
                f"{candidate['tmdb_id']}"
            )

            print(
                f"   Original  : "
                f"{candidate['original_title']}"
            )

            print(
                f"   Date      : "
                f"{candidate['release_date']}"
            )

            print(
                f"   Score     : "
                f"{candidate['score']}"
            )

            print(
                f"   Reasons   : "
                f"{', '.join(candidate.get('reasons', []))}"
            )

            print()

    print()
    print("=" * 90)
    print(
        f"TOTAL REVIEW: {review_count}"
    )
    print("=" * 90)


if __name__ == "__main__":
    main()