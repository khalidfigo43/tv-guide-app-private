import json
from collections import Counter
from pathlib import Path


FILE = Path("data/rotana_schedule.json")


def main():
    # ---------------------------------------------------------
    # Load data
    # ---------------------------------------------------------

    if not FILE.exists():
        print(f"ERROR: File not found: {FILE}")
        return

    try:
        data = json.loads(
            FILE.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        return

    programs = data.get("data", [])

    print("=" * 70)
    print("ROTANA DATA VALIDATION")
    print("=" * 70)

    print(f"Total records: {len(programs)}")

    # ---------------------------------------------------------
    # Programs per channel
    # ---------------------------------------------------------

    print("\nPrograms per channel:")
    print("-" * 70)

    channels = Counter(
        p.get("channelName")
        for p in programs
    )

    for channel, count in channels.items():
        print(f"{channel}: {count}")

    # ---------------------------------------------------------
    # Dates
    # ---------------------------------------------------------

    print("\nDates:")
    print("-" * 70)

    dates = Counter(
        p.get("date")
        for p in programs
    )

    # None comes after real dates
    for date, count in sorted(
        dates.items(),
        key=lambda x: (
            x[0] is None,
            x[0] or ""
        )
    ):
        print(f"{date}: {count}")

    # ---------------------------------------------------------
    # Missing fields
    # ---------------------------------------------------------

    print("\nMissing fields:")
    print("-" * 70)

    fields = [
        "channelId",
        "channelName",
        "sourceItemId",
        "date",
        "startTime",
        "title",
    ]

    for field in fields:
        missing = sum(
            1
            for p in programs
            if not p.get(field)
        )

        percentage = (
            (missing / len(programs)) * 100
            if programs
            else 0
        )

        print(
            f"{field}: "
            f"{missing} missing "
            f"({percentage:.1f}%)"
        )

    # ---------------------------------------------------------
    # Records with missing date
    # ---------------------------------------------------------

    missing_date = [
        p
        for p in programs
        if not p.get("date")
    ]

    print("\nRecords with missing date:")
    print("-" * 70)
    print(f"Count: {len(missing_date)}")

    for p in missing_date[:20]:
        print(
            f'Channel: {p.get("channelName")} | '
            f'Time: {p.get("startTime")} | '
            f'Title: {p.get("title")} | '
            f'ID: {p.get("sourceItemId")}'
        )

    if len(missing_date) > 20:
        print(
            f"... and {len(missing_date) - 20} more"
        )

    # ---------------------------------------------------------
    # Duplicate records
    # ---------------------------------------------------------

    print("\nDuplicate records:")
    print("-" * 70)

    seen = {}
    duplicates = []

    for p in programs:
        key = (
            p.get("channelId"),
            p.get("sourceItemId"),
            p.get("date"),
            p.get("startTime"),
        )

        if key in seen:
            duplicates.append(p)
        else:
            seen[key] = p

    print(f"Duplicates: {len(duplicates)}")

    for p in duplicates[:20]:
        print(
            f'Channel: {p.get("channelName")} | '
            f'Date: {p.get("date")} | '
            f'Time: {p.get("startTime")} | '
            f'Title: {p.get("title")} | '
            f'ID: {p.get("sourceItemId")}'
        )

    if len(duplicates) > 20:
        print(
            f"... and {len(duplicates) - 20} more"
        )

    # ---------------------------------------------------------
    # Sample records
    # ---------------------------------------------------------

    print("\nSample records:")
    print("-" * 70)

    for p in programs[:15]:
        print(
            f'{p.get("date")} | '
            f'{p.get("startTime")} | '
            f'{p.get("channelName")} | '
            f'{p.get("title")} | '
            f'ID={p.get("sourceItemId")}'
        )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    print(f"Total records : {len(programs)}")
    print(f"Channels      : {len(channels)}")
    print(f"Missing dates : {len(missing_date)}")
    print(f"Duplicates    : {len(duplicates)}")

    print("\nDone.")


if __name__ == "__main__":
    main()