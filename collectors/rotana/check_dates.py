import json
from collections import defaultdict
from pathlib import Path

FILE = Path("data/rotana_schedule.json")

data = json.loads(
    FILE.read_text(encoding="utf-8")
)

programs = data["data"]

by_channel = defaultdict(lambda: defaultdict(list))

for p in programs:
    by_channel[p["channelName"]][p["date"]].append(p)


print("=" * 90)
print("DATE DISTRIBUTION BY CHANNEL")
print("=" * 90)

for channel, dates in by_channel.items():

    print("\n" + channel)
    print("-" * 90)

    for date in sorted(dates.keys()):
        items = dates[date]

        print(
            f"{date}: {len(items)} programs"
        )

        # أول 3 وآخر 2 برامج في اليوم
        for p in items[:3]:
            print(
                f"    {p['startTime']} | "
                f"{p['title']} | "
                f"ID={p['sourceItemId']}"
            )

        if len(items) > 5:
            print("    ...")

        for p in items[-2:]:
            print(
                f"    {p['startTime']} | "
                f"{p['title']} | "
                f"ID={p['sourceItemId']}"
            )


print("\n" + "=" * 90)
print("DONE")
print("=" * 90)