"""
TV Guide - Comprehensive Architecture & Logic Verification Suite
Tests all 5 core requirements:
1. Current is always the actually-running program regardless of category.
2. Next is the earliest upcoming program regardless of category.
3. The content listing follows: Movies Arabic -> Movies English/Foreign -> Series -> Cartoons/Kids -> Other.
4. Each category is chronologically sorted (date ASC, startTime ASC).
5. Crossing midnight does not break Current/Next.
6. Delta generation and incremental sync verification.
"""

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def parse_dt(d_str, t_str, allow_next_day=False):
    dt = datetime.strptime(f"{d_str} {t_str}", "%Y-%m-%d %H:%M")
    if allow_next_day:
        dt += timedelta(days=1)
    return dt


def get_current_next_for_channel(channel_schedules, target_dt):
    """Strictly time-based Current/Next calculation for a single channel."""
    current = None
    # 1. Match current
    valid_currents = []
    for s in channel_schedules:
        st = s["startTime"]
        et = s["endTime"]
        d = s["date"]
        s_dt = parse_dt(d, st)
        e_dt = parse_dt(d, et, allow_next_day=et < st)
        if s_dt <= target_dt < e_dt:
            valid_currents.append((s_dt, s))

    if valid_currents:
        # Pick most recently started if multiple
        valid_currents.sort(key=lambda x: x[0], reverse=True)
        current = valid_currents[0][1]

    # 2. Match next (earliest strictly after target_dt)
    upcoming = []
    for s in channel_schedules:
        st = s["startTime"]
        d = s["date"]
        s_dt = parse_dt(d, st)
        if s_dt > target_dt:
            upcoming.append((s_dt, s))

    next_prog = None
    if upcoming:
        upcoming.sort(key=lambda x: x[0])
        next_prog = upcoming[0][1]

    return current, next_prog


def get_content_browse_tier(program_type, title, channel_name):
    t = (program_type or "").lower()
    tit = (title or "").lower()
    ch = (channel_name or "").lower()

    is_movie = (
        "movie" in t or "film" in t or "cinema" in t or
        tit.startswith("فيلم") or tit.startswith("فلم") or
        "cinema" in ch or "سينما" in ch or "movies" in ch or "أفلام" in ch or
        "mbc 2" in ch or "mbc max" in ch or "mbc action" in ch or "fox" in ch
    )

    if is_movie:
        # Check Arabic vs English
        is_arabic = any('\u0600' <= c <= '\u06FF' for c in (title or "")) and not any(k in ch for k in ["osn", "mbc 2", "mbc max", "mbc action", "fox"])
        return 1 if is_arabic else 2

    is_series = "series" in t or "drama" in t or "مسلسل" in t or "دراما" in t or "حلقة" in tit or "series" in ch or "دراما" in ch
    if is_series:
        return 3

    is_cartoon = t in ["cartoon", "animation", "anime", "kids", "children"] or "كرتون" in t or "أطفال" in t or "spacetoon" in ch or "سبيستون" in ch or "cartoon" in ch or "cn" in ch
    if is_cartoon:
        return 4

    return 5


def test_1_current_strictly_time_based():
    print("\n--- TEST 1: Current is always the actually-running program regardless of category ---")
    # Channel schedule:
    # 18:00 - 20:00: Movie (The Matrix)
    # 20:00 - 21:00: Cartoon (Tom & Jerry)
    # 21:00 - 23:00: Arabic Movie (ساعة ونص)
    schedules = [
        {"channelId": 10, "title": "The Matrix", "programType": "movie", "date": "2026-09-02", "startTime": "18:00", "endTime": "20:00"},
        {"channelId": 10, "title": "Tom & Jerry", "programType": "cartoon", "date": "2026-09-02", "startTime": "20:00", "endTime": "21:00"},
        {"channelId": 10, "title": "ساعة ونص", "programType": "movie", "date": "2026-09-02", "startTime": "21:00", "endTime": "23:00"},
    ]

    target_time = parse_dt("2026-09-02", "20:30")
    cur, nxt = get_current_next_for_channel(schedules, target_time)

    assert cur is not None, "Current should not be None"
    assert cur["title"] == "Tom & Jerry", f"Expected 'Tom & Jerry' (cartoon) to be Current at 20:30, but got '{cur['title']}'!"
    print("✓ PASS: Cartoon running at 20:30 correctly identified as Current (Movie at 21:00 did NOT usurp it).")


def test_2_next_strictly_time_based():
    print("\n--- TEST 2: Next is the earliest upcoming program regardless of category ---")
    schedules = [
        {"channelId": 10, "title": "Tom & Jerry", "programType": "cartoon", "date": "2026-09-02", "startTime": "20:00", "endTime": "21:00"},
        {"channelId": 10, "title": "مسلسل الاختيار", "programType": "series", "date": "2026-09-02", "startTime": "21:00", "endTime": "22:00"},
        {"channelId": 10, "title": "فيلم البدلة", "programType": "movie", "date": "2026-09-02", "startTime": "22:00", "endTime": "00:00"},
    ]

    target_time = parse_dt("2026-09-02", "20:30")
    cur, nxt = get_current_next_for_channel(schedules, target_time)

    assert nxt is not None, "Next should not be None"
    assert nxt["title"] == "مسلسل الاختيار", f"Expected earliest next 'مسلسل الاختيار' (series), got '{nxt['title']}'"
    print("✓ PASS: Series at 21:00 correctly chosen as Next over Movie at 22:00.")


def test_3_and_4_content_listing_5_tiers_chronological():
    print("\n--- TEST 3 & 4: 5-Tier Content Listing Priority & Chronological Sorting ---")
    items = [
        {"title": "The Dark Knight", "programType": "movie", "channelName": "OSN Movies", "date": "2026-09-02", "startTime": "22:00"},
        {"title": "فيلم كيرة والجن", "programType": "movie", "channelName": "روتانا سينما", "date": "2026-09-02", "startTime": "23:00"},
        {"title": "فيلم ساعة ونص", "programType": "movie", "channelName": "روتانا سينما", "date": "2026-09-02", "startTime": "20:00"},
        {"title": "مسلسل جعفر العمدة", "programType": "series", "channelName": "DMC دراما", "date": "2026-09-02", "startTime": "21:00"},
        {"title": "سبونج بوب", "programType": "cartoon", "channelName": "سبيستون", "date": "2026-09-02", "startTime": "19:00"},
        {"title": "برنامج معكم منى الشاذلي", "programType": "program", "channelName": "ON E", "date": "2026-09-02", "startTime": "18:00"},
        {"title": "Inception", "programType": "movie", "channelName": "MBC 2", "date": "2026-09-02", "startTime": "20:30"},
        {"title": "المحقق كونان", "programType": "cartoon", "channelName": "سبيستون", "date": "2026-09-02", "startTime": "17:00"},
        {"title": "مسلسل الحشاشين", "programType": "series", "channelName": "DMC دراما", "date": "2026-09-02", "startTime": "19:30"},
    ]

    for it in items:
        it["tier"] = get_content_browse_tier(it["programType"], it["title"], it["channelName"])

    # Sort strictly by Tier ASC, then date ASC, startTime ASC
    items.sort(key=lambda x: (x["tier"], x["date"], x["startTime"]))

    print("Sorted Content List Result:")
    for idx, it in enumerate(items, 1):
        print(f"  {idx}. [Tier {it['tier']}] {it['startTime']} : {it['title']} ({it['channelName']})")

    # Verify tiers order
    tiers = [it["tier"] for it in items]
    assert tiers == [1, 1, 2, 2, 3, 3, 4, 4, 5], f"Tiers out of order: {tiers}"

    # Verify chronological within Arabic movies (Tier 1)
    arabic_movies = [it for it in items if it["tier"] == 1]
    assert arabic_movies[0]["startTime"] == "20:00" and arabic_movies[1]["startTime"] == "23:00"

    # Verify chronological within Foreign movies (Tier 2)
    foreign_movies = [it for it in items if it["tier"] == 2]
    assert foreign_movies[0]["startTime"] == "20:30" and foreign_movies[1]["startTime"] == "22:00"

    # Verify chronological within Series (Tier 3)
    series_list = [it for it in items if it["tier"] == 3]
    assert series_list[0]["startTime"] == "19:30" and series_list[1]["startTime"] == "21:00"

    # Verify chronological within Cartoons (Tier 4)
    cartoons = [it for it in items if it["tier"] == 4]
    assert cartoons[0]["startTime"] == "17:00" and cartoons[1]["startTime"] == "19:00"

    print("✓ PASS: Content list strictly follows Arabic Movies -> Foreign Movies -> Series -> Cartoons -> Other.")
    print("✓ PASS: Every category is sorted chronologically (earliest time first).")


def test_5_midnight_crossing():
    print("\n--- TEST 5: Crossing Midnight does not break Current/Next ---")
    schedules = [
        {"channelId": 1, "title": "سهرة منتصف الليل", "programType": "movie", "date": "2026-09-02", "startTime": "23:30", "endTime": "01:30"},
        {"channelId": 1, "title": "حديث الصباح", "programType": "program", "date": "2026-09-03", "startTime": "01:30", "endTime": "03:00"},
    ]

    # Test time is 00:45 AM on September 3rd (15 mins after midnight)
    target_time = parse_dt("2026-09-03", "00:45")
    cur, nxt = get_current_next_for_channel(schedules, target_time)

    assert cur is not None, "Current at 00:45 should not be None"
    assert cur["title"] == "سهرة منتصف الليل", f"Expected 'سهرة منتصف الليل' across midnight, got {cur['title']}"
    assert nxt is not None, "Next should not be None"
    assert nxt["title"] == "حديث الصباح", f"Expected 'حديث الصباح' at 01:30, got {nxt['title']}"
    print("✓ PASS: 23:30 -> 01:30 broadcast correctly identified as Current at 00:45 AM after midnight.")
    print("✓ PASS: 01:30 broadcast correctly identified as Next.")


def test_6_delta_generation_metrics():
    print("\n--- TEST 6: Delta Generation & Bandwidth Verification ---")
    from scripts.generate_delta import generate_delta

    prev_sample = [
        {"channelId": 1, "title": "Movie A", "date": "2026-09-02", "startTime": "10:00", "endTime": "12:00", "programType": "movie"},
        {"channelId": 1, "title": "Movie B", "date": "2026-09-02", "startTime": "12:00", "endTime": "14:00", "programType": "movie"},
        {"channelId": 1, "title": "Movie C Old", "date": "2026-09-02", "startTime": "14:00", "endTime": "16:00", "programType": "movie"},
    ]

    curr_sample = [
        # Movie A retained
        {"channelId": 1, "title": "Movie A", "date": "2026-09-02", "startTime": "10:00", "endTime": "12:00", "programType": "movie"},
        # Movie B deleted (pruned)
        # Movie C updated title
        {"channelId": 1, "title": "Movie C New", "date": "2026-09-02", "startTime": "14:00", "endTime": "16:00", "programType": "movie"},
        # Movie D added
        {"channelId": 1, "title": "Movie D Added", "date": "2026-09-02", "startTime": "16:00", "endTime": "18:00", "programType": "movie"},
    ]

    delta = generate_delta(prev_sample, curr_sample, 101, 102)

    assert delta["summary"]["addedCount"] == 1, f"Expected 1 added, got {delta['summary']['addedCount']}"
    assert delta["summary"]["updatedCount"] == 1, f"Expected 1 updated, got {delta['summary']['updatedCount']}"
    assert delta["summary"]["deletedCount"] == 1, f"Expected 1 deleted, got {delta['summary']['deletedCount']}"
    print(f"✓ PASS: Delta correctly computed Added: {delta['summary']['addedCount']}, Updated: {delta['summary']['updatedCount']}, Deleted: {delta['summary']['deletedCount']}")


def main():
    print("=" * 80)
    print("RUNNING COMPREHENSIVE ARCHITECTURE VERIFICATION TEST SUITE")
    print("=" * 80)

    test_1_current_strictly_time_based()
    test_2_next_strictly_time_based()
    test_3_and_4_content_listing_5_tiers_chronological()
    test_5_midnight_crossing()
    test_6_delta_generation_metrics()

    print("\n" + "=" * 80)
    print("🎉 ALL 6 ARCHITECTURAL TESTS PASSED SUCCESSFULLY 100%!")
    print("=" * 80)


if __name__ == "__main__":
    main()
