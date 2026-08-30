import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://rotana.net/ar/streams"

CHANNELS = {
    431: "روتانا سينما السعودية",
    434: "إل بي سي",
    435: "روتانا خليجية",
    436: "روتانا دراما",
    437: "روتانا كوميدي",
    438: "روتانا كلاسيك",
    439: "روتانا سينما مصر",
    446: "الرسالة",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
}

DATE_PATTERN = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
TIME_PATTERN = re.compile(r"\b([01]\d|2[0-3]):[0-5]\d\b")


def get_page(channel_id):
    response = requests.get(
        BASE_URL,
        params={"channel": channel_id},
        headers=HEADERS,
        timeout=30,
    )

    response.raise_for_status()

    return response.text


def parse_schedule(html, channel_id, channel_name):
    soup = BeautifulSoup(html, "html.parser")

    programs = []
    current_date = None

    for element in soup.find_all(True):

        element_id = element.get("id", "")

        if not element_id:
            continue

        text = element.get_text(" ", strip=True)

        # -----------------------------------------------------
        # Date header
        # -----------------------------------------------------

        date_match = DATE_PATTERN.search(text)

        if date_match:
            current_date = date_match.group(1)
            continue

        # -----------------------------------------------------
        # Program item
        # -----------------------------------------------------

        item_match = re.fullmatch(
            r"item-(\d+)",
            element_id
        )

        if not item_match:
            continue

        source_item_id = int(item_match.group(1))

        time_match = TIME_PATTERN.search(text)

        if not time_match:
            continue

        start_time = time_match.group(0)

        # -----------------------------------------------------
        # Title
        # -----------------------------------------------------

        title = text

        title = TIME_PATTERN.sub("", title)
        title = DATE_PATTERN.sub("", title)
        title = title.strip()

        if not title:
            continue

        # Convert UTC from Rotana API to Cairo/KSA Local Time (UTC+3)
        try:
            raw_dt = datetime.strptime(f"{current_date} {start_time}", "%Y-%m-%d %H:%M")
            local_dt = raw_dt + timedelta(hours=3)
            local_date = local_dt.strftime("%Y-%m-%d")
            local_start_time = local_dt.strftime("%H:%M")
        except Exception:
            local_date = current_date
            local_start_time = start_time

        programs.append({
            "source": "rotana",
            "channelId": channel_id,
            "channelName": channel_name,
            "sourceItemId": source_item_id,
            "date": local_date,
            "startTime": local_start_time,
            "endTime": None,
            "endDate": None,
            "title": title,
        })

    return programs


def add_end_times(programs):
    """
    بداية البرنامج التالي = نهاية البرنامج الحالي.

    مثال:

    10:00 A
    12:00 B

    A:
    10:00 -> 12:00

    ولو:

    23:00 A
    01:00 B

    A:
    23:00 -> 01:00 في اليوم التالي
    """

    # ---------------------------------------------------------
    # Group by channel
    # ---------------------------------------------------------

    by_channel = {}

    for program in programs:
        channel_id = program["channelId"]

        by_channel.setdefault(
            channel_id,
            []
        ).append(program)

    # ---------------------------------------------------------
    # Process each channel
    # ---------------------------------------------------------

    for channel_programs in by_channel.values():

        # إزالة أي سجل بدون تاريخ أو وقت
        valid_programs = [
            p for p in channel_programs
            if p.get("date") and p.get("startTime")
        ]

        # ترتيب زمني حقيقي
        valid_programs.sort(
            key=lambda p: datetime.strptime(
                f'{p["date"]} {p["startTime"]}',
                "%Y-%m-%d %H:%M"
            )
        )

        for i, current in enumerate(valid_programs):

            # لا يوجد برنامج بعده
            if i + 1 >= len(valid_programs):
                current["endTime"] = None
                current["endDate"] = None
                continue

            next_program = valid_programs[i + 1]

            current["endTime"] = next_program["startTime"]
            current["endDate"] = next_program["date"]

    return programs


def collect_channel(channel_id, channel_name):
    print()
    print(f"[{channel_id}] {channel_name}")
    print("-" * 60)

    try:
        html = get_page(channel_id)

        print(f"HTML size: {len(html):,}")

        programs = parse_schedule(
            html,
            channel_id,
            channel_name,
        )

        print(f"Programs found: {len(programs)}")

        return programs

    except Exception as e:
        print(f"ERROR: {e}")
        return []


def main():

    all_programs = []

    # ---------------------------------------------------------
    # Collect all channels
    # ---------------------------------------------------------

    for channel_id, channel_name in CHANNELS.items():

        programs = collect_channel(
            channel_id,
            channel_name,
        )

        all_programs.extend(programs)

        # تقليل الضغط على المصدر
        time.sleep(1)

    # ---------------------------------------------------------
    # Calculate end times
    # ---------------------------------------------------------

    all_programs = add_end_times(
        all_programs
    )

    # ---------------------------------------------------------
    # Remove duplicates
    # ---------------------------------------------------------

    unique = {}

    for program in all_programs:

        key = (
            program["channelId"],
            program["sourceItemId"],
            program["date"],
            program["startTime"],
        )

        unique[key] = program

    # ---------------------------------------------------------
    # Result
    # ---------------------------------------------------------

    result = {
        "source": "rotana",
        "channels": len(CHANNELS),
        "programs": len(unique),
        "data": list(unique.values()),
    }

    # ---------------------------------------------------------
    # Save
    # ---------------------------------------------------------

    output_path = Path(
        "data/rotana_schedule.json"
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)

    print(f"Channels : {len(CHANNELS)}")
    print(f"Programs : {len(unique)}")
    print(f"Output   : {output_path}")


if __name__ == "__main__":
    main()