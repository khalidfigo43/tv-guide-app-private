import json
import os
import re
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collectors.channels_catalog import ALL_CHANNELS_CATALOG


def get_cairo_today() -> str:
    """Returns today's date in Africa/Cairo timezone (UTC+2 or UTC+3)."""
    try:
        import zoneinfo
        return datetime.now(zoneinfo.ZoneInfo("Africa/Cairo")).strftime("%Y-%m-%d")
    except Exception:
        return (datetime.utcnow() + timedelta(hours=3)).strftime("%Y-%m-%d")


def load_existing_schedules() -> List[Dict[str, Any]]:
    for path in [
        Path("data/schedules.json"),
        Path("android/app/src/main/assets/schedules.json")
    ]:
        if path.exists():
            try:
                content = path.read_text(encoding="utf-8").strip()
                if content:
                    parsed = json.loads(content)
                    if isinstance(parsed, list):
                        return parsed
                    elif isinstance(parsed, dict) and "schedules" in parsed:
                        return parsed["schedules"]
            except Exception as e:
                print(f"Warning loading existing {path}: {e}")
    return []


def run_all_collectors() -> Tuple[List[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Runs all collectors: Rotana, OSN, and ElCinema.
    Returns (all_fresh_items, collector_reports).
    """
    collector_reports = {}
    fresh_items = []

    # 1. Rotana Collector
    print("\n" + "=" * 70)
    print("STEP 1: RUNNING ROTANA DYNAMIC COLLECTOR")
    print("=" * 70)
    try:
        from collectors.rotana.collector import run_collector as run_rotana
        rot_res = run_rotana()
        collector_reports["rotana"] = {
            "name": "Rotana",
            "status": rot_res.get("status", "UNKNOWN"),
            "channels_attempted": rot_res.get("channels_attempted", 0),
            "channels_succeeded": rot_res.get("channels_succeeded", 0),
            "broadcasts_count": rot_res.get("broadcasts_count", 0),
            "min_date": rot_res.get("min_date"),
            "max_date": rot_res.get("max_date"),
        }
        fresh_items.extend(rot_res.get("data", []))
    except Exception as e:
        print(f"❌ Rotana collector exception: {e}")
        collector_reports["rotana"] = {
            "name": "Rotana",
            "status": "COLLECTOR_FAILED",
            "error": str(e),
            "channels_attempted": 8,
            "channels_succeeded": 0,
            "broadcasts_count": 0,
            "min_date": None,
            "max_date": None,
        }

    # 2. OSN Official Collector
    print("\n" + "=" * 70)
    print("STEP 2: RUNNING OSN DYNAMIC TIMELINE COLLECTOR")
    print("=" * 70)
    try:
        from collectors.osn.collector import run_collector as run_osn
        osn_res = run_osn()
        collector_reports["osn"] = {
            "name": "OSN",
            "status": osn_res.get("status", "UNKNOWN"),
            "channels_attempted": osn_res.get("channels_attempted", 0),
            "channels_succeeded": osn_res.get("channels_succeeded", 0),
            "broadcasts_count": osn_res.get("broadcasts_count", 0),
            "min_date": osn_res.get("min_date"),
            "max_date": osn_res.get("max_date"),
        }
        fresh_items.extend(osn_res.get("data", []))
    except Exception as e:
        print(f"❌ OSN collector exception: {e}")
        collector_reports["osn"] = {
            "name": "OSN",
            "status": "COLLECTOR_FAILED",
            "error": str(e),
            "channels_attempted": 100,
            "channels_succeeded": 0,
            "broadcasts_count": 0,
            "min_date": None,
            "max_date": None,
        }

    # 3. ElCinema Live Collector
    print("\n" + "=" * 70)
    print("STEP 3: RUNNING ELCINEMA DYNAMIC MULTI-CHANNEL COLLECTOR")
    print("=" * 70)
    try:
        from sync_accurate_elcinema import run_collector as run_elcinema
        elc_res = run_elcinema(max_workers=4)
        collector_reports["elcinema"] = {
            "name": "ElCinema",
            "status": elc_res.get("status", "UNKNOWN"),
            "channels_attempted": elc_res.get("channels_attempted", 0),
            "channels_succeeded": elc_res.get("channels_succeeded", 0),
            "broadcasts_count": elc_res.get("broadcasts_count", 0),
            "min_date": elc_res.get("min_date"),
            "max_date": elc_res.get("max_date"),
        }
        fresh_items.extend(elc_res.get("data", []))
    except Exception as e:
        print(f"❌ ElCinema collector exception: {e}")
        collector_reports["elcinema"] = {
            "name": "ElCinema",
            "status": "COLLECTOR_FAILED",
            "error": str(e),
            "channels_attempted": 109,
            "channels_succeeded": 0,
            "broadcasts_count": 0,
            "min_date": None,
            "max_date": None,
        }

    return fresh_items, collector_reports


def normalize_schedule_key(item: Dict[str, Any]) -> Tuple[Any, str, str]:
    """Generates unique primary key for a broadcast: (channelId, date, startTime)."""
    ch_id = item.get("channelId")
    date_str = str(item.get("date") or "").strip()
    start_time = str(item.get("startTime") or "").strip()
    return (ch_id, date_str, start_time)


def merge_and_upsert_schedules(
    existing_schedules: List[Dict[str, Any]],
    fresh_items: List[Dict[str, Any]],
    today_str: str,
    catalog_by_id: Dict[int, Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Performs true MERGE / UPSERT:
    - Retains existing valid future broadcasts (date >= today).
    - Upserts fresh items into existing slots.
    - Prunes past broadcasts (date < today).
    - Enriches with catalog logos, types, ratings, and posters.
    """
    print("\n" + "=" * 70)
    print("STEP 4: MERGE & UPSERT PIPELINE")
    print("=" * 70)

    stats = {
        "existing_input": len(existing_schedules),
        "fresh_input": len(fresh_items),
        "updated": 0,
        "inserted": 0,
        "retained_future": 0,
        "pruned_past": 0,
    }
    retention_cutoff = (datetime.strptime(today_str, "%Y-%m-%d") - timedelta(days=3)).strftime("%Y-%m-%d")

    ESPORTS_KEYWORDS = {"esport", "e-sport", "eclutch", "gametoon", "ginx", "gaming", "العاب"}
    DELETED_CHANNEL_IDS = {91, 179, 196, 200, 203, 204, 216, 217, 234, 235, 236, 238, 239, 240, 241, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260}
    DELETED_KEYWORDS = {"kapatid", "rfm tv", "mcm top", "dzmm", "teleradyo", "mor global", "rt english", "rt arabic", "روسيا اليوم", "cinemo", "gma pinoy", "gma life", "padel", "anc", "stv1", "stv 1", "تلفزيون البحرين", "bahrain tv"}

    def is_esports(name: str) -> bool:
        if not name:
            return False
        n = str(name).lower()
        return any(k in n for k in ESPORTS_KEYWORDS)

    def is_deleted(ch_id: Any, name: str) -> bool:
        if ch_id in DELETED_CHANNEL_IDS:
            return True
        if not name:
            return False
        n = str(name).lower()
        return any(k in n for k in DELETED_KEYWORDS)

    # Identify channel-dates covered by authoritative ElCinema Cairo broadcasts
    elcinema_channel_dates = set(
        (it.get("channelId"), it.get("date"))
        for it in fresh_items
        if it.get("source") == "elcinema_live" and it.get("channelId") and it.get("date")
    )

    title_to_poster = {}
    title_to_overview = {}
    title_to_cast = {}
    title_to_type = {}

    for s in existing_schedules:
        if is_esports(s.get("channelName")) or is_deleted(s.get("channelId"), s.get("channelName")):
            continue
        t = s.get("title")
        if t:
            if s.get("poster") and not str(s.get("poster", "")).startswith("data:"):
                title_to_poster[t] = s.get("poster")
            if s.get("overview"):
                title_to_overview[t] = s.get("overview")
            if s.get("cast"):
                title_to_cast[t] = s.get("cast")
            if s.get("programType"):
                title_to_type[t] = s.get("programType")

    merged_map: Dict[Tuple[Any, str, str], Dict[str, Any]] = {}

    for s in existing_schedules:
        if is_esports(s.get("channelName")):
            continue
        item_date = s.get("date")
        if not item_date:
            continue

        # Prune broadcasts strictly older than retention cutoff (last 3 days retained)
        if item_date < retention_cutoff:
            stats["pruned_past"] += 1
            continue

        # If this channel-date is now covered by fresh ElCinema, don't keep old unaligned items
        ch_id = s.get("channelId")
        if (ch_id, item_date) in elcinema_channel_dates:
            continue

        key = normalize_schedule_key(s)
        merged_map[key] = dict(s)
        stats["retained_future"] += 1

    # Upsert fresh items
    for item in fresh_items:
        ch_id = item.get("channelId")
        if ch_id is None or not item.get("date") or not item.get("startTime"):
            continue

        item_date = item.get("date")
        if item_date < retention_cutoff:
            continue

        ch_info = catalog_by_id.get(ch_id, {})
        ch_name = item.get("channelName") or ch_info.get("name_ar") or f"Channel {ch_id}"
        if is_esports(ch_name) or is_esports(item.get("title", "")) or is_deleted(ch_id, ch_name):
            continue

        # If this channel-date is covered by ElCinema, ignore conflicting web scrape
        if item.get("source") == "rotana" and (ch_id, item_date) in elcinema_channel_dates:
            continue

        key = normalize_schedule_key(item)
        ch_info = catalog_by_id.get(ch_id, {})
        ch_name = item.get("channelName") or ch_info.get("name_ar") or f"Channel {ch_id}"
        ch_logo = item.get("channelLogo") or ch_info.get("logo_url")
        is_paid = item.get("is_paid", ch_info.get("is_paid", False))
        title = item.get("title", "").strip()

        poster = item.get("poster") or title_to_poster.get(title) or ch_logo
        overview = item.get("overview") or title_to_overview.get(title, f"عرض تلفزيوني على {ch_name}")
        program_type = item.get("programType") or title_to_type.get(
            title,
            "movie" if "سينما" in ch_name or "أفلام" in ch_name or "movies" in ch_name.lower()
            else "series" if "دراما" in ch_name or "مسلسلات" in ch_name or "series" in ch_name.lower()
            else "program"
        )
        cast = item.get("cast") or title_to_cast.get(title, [])
        rating = item.get("rating") or "7.5"

        standard_item = {
            "channelId": ch_id,
            "channelName": ch_name,
            "channelLogo": ch_logo,
            "title": title,
            "title_en": item.get("title_en"),
            "date": item_date,
            "startTime": item.get("startTime"),
            "endTime": item.get("endTime"),
            "poster": poster,
            "overview": overview,
            "programType": program_type,
            "rating": rating,
            "cast": cast,
            "is_paid": is_paid
        }

        if key in merged_map:
            stats["updated"] += 1
        else:
            stats["inserted"] += 1

        merged_map[key] = standard_item

    result_list = list(merged_map.values())
    result_list.sort(key=lambda x: (x.get("date", ""), x.get("startTime", ""), x.get("channelId", 0)))

    print(f"✓ Merge complete:")
    print(f"  Existing retained future items: {stats['retained_future']}")
    print(f"  Pruned past items (< {today_str}): {stats['pruned_past']}")
    print(f"  Fresh items added: {stats['inserted']}")
    print(f"  Existing items updated: {stats['updated']}")
    print(f"  Final total broadcast entries: {len(result_list)}")

    return result_list, stats


def validate_schedules(
    schedules: List[Dict[str, Any]],
    baseline_count: int,
    today_str: str,
    collector_reports: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Strict Baseline & Quality Validation:
    - Not abnormally empty.
    - No unexpected duplicates on (channelId, date, startTime).
    - No fake/rewritten dates.
    - Preserves expected channels and records volume against baseline.
    """
    print("\n" + "=" * 70)
    print("STEP 5: VALIDATION GUARD")
    print("=" * 70)

    errors = []
    warnings = []

    if not schedules:
        errors.append("Validation failed: final schedule dataset is completely empty!")

    channels_with_data = len(set(s.get("channelId") for s in schedules if s.get("channelId")))

    if baseline_count > 0:
        min_allowed = int(baseline_count * 0.4)
        if len(schedules) < min_allowed:
            if channels_with_data >= 40 and len(schedules) >= 2000:
                warnings.append(
                    f"Notice: Fresh dataset has {len(schedules)} broadcasts (< 40% of previous multi-week baseline {baseline_count}). "
                    f"Accepting reset with {channels_with_data} active channels after staleness gap."
                )
            else:
                errors.append(f"Abnormal record collapse! Count {len(schedules)} is < 40% of baseline {baseline_count}")

    if channels_with_data < 50:
        errors.append(f"Abnormal channel collapse! Only {channels_with_data} channels have schedules (expected >= 50).")

    dates = sorted(set(s.get("date") for s in schedules if s.get("date")))
    if not dates:
        errors.append("No dates found in schedule dataset!")
    else:
        min_date = dates[0]
        max_date = dates[-1]

        past_dates = [d for d in dates if d < today_str]
        if past_dates:
            warnings.append(f"Dataset contains {len(past_dates)} past dates older than today ({past_dates})")

        if max_date <= today_str:
            future_collectors = [c for c, r in collector_reports.items() if r.get("status") == "SUCCESS_WITH_FUTURE"]
            if future_collectors:
                errors.append(f"Collectors {future_collectors} reported future dates, but final dataset max date is only {max_date}!")
            else:
                warnings.append(f"No future dates found in any collector. Max date is today ({today_str}).")

    seen_keys = set()
    dupe_count = 0
    for s in schedules:
        k = (s.get("channelId"), s.get("date"), s.get("startTime"))
        if k in seen_keys:
            dupe_count += 1
        seen_keys.add(k)

    if dupe_count > 0:
        errors.append(f"Found {dupe_count} duplicate broadcasts with identical (channelId, date, startTime)!")

    if errors:
        print("❌ VALIDATION FAILED WITH ERRORS:")
        for err in errors:
            print(f"   • {err}")
        return {"is_valid": False, "errors": errors, "warnings": warnings}

    if warnings:
        print("⚠️ Validation passed with warnings:")
        for w in warnings:
            print(f"   • {w}")

    print(f"✓ All validation checks passed successfully!")
    print(f"  Channels with data: {channels_with_data}")
    print(f"  Total broadcasts  : {len(schedules)}")
    print(f"  Date range        : {dates[0] if dates else 'N/A'} -> {dates[-1] if dates else 'N/A'}")
    return {"is_valid": True, "errors": [], "warnings": warnings}


def main():
    start_time = time.time()
    today_str = get_cairo_today()
    utc_now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    cairo_now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("=" * 80)
    print("TV GUIDE - PRODUCTION MULTI-SOURCE PIPELINE & DYNAMIC MERGE ENGINE")
    print(f"Execution Date (Africa/Cairo): {today_str}")
    print(f"UTC Timestamp                : {utc_now_iso}")
    print("=" * 80)

    # 1. Load baseline
    existing_schedules = load_existing_schedules()
    baseline_count = len(existing_schedules)
    print(f"[*] Loaded existing schedules baseline: {baseline_count} broadcasts")

    # 2. Map catalog
    catalog_by_id = {c["id"]: c for c in ALL_CHANNELS_CATALOG}

    # 3. Run collectors
    fresh_items, collector_reports = run_all_collectors()

    # 4. Merge and upsert
    merged_schedules, merge_stats = merge_and_upsert_schedules(
        existing_schedules=existing_schedules,
        fresh_items=fresh_items,
        today_str=today_str,
        catalog_by_id=catalog_by_id
    )

    # 5. Validate
    validation_res = validate_schedules(
        schedules=merged_schedules,
        baseline_count=baseline_count,
        today_str=today_str,
        collector_reports=collector_reports
    )

    if not validation_res["is_valid"]:
        print("\n❌ ABORTING PUBLICATION: Dataset did not pass validation guard.")
        sys.exit(1)

    # 6. Build Channel Profiles & Smart Centralized Content Classification
    from classifier.content_classifier import ChannelProfiler, ContentClassifier, CanonicalContentType, CONTENT_PRIORITY

    schedules_by_channel = {}
    for s in merged_schedules:
        ch_id = s.get("channelId")
        if ch_id:
            schedules_by_channel.setdefault(ch_id, []).append(s)

    channel_profiles = {}
    for ch in ALL_CHANNELS_CATALOG:
        ch_id = ch["id"]
        ch_name = ch.get("name_ar") or ch.get("name_en") or f"Channel {ch_id}"
        ch_cat = ch.get("category")
        prof = ChannelProfiler.build_profile(
            channel_id=ch_id,
            channel_name=ch_name,
            category=ch_cat,
            schedules=schedules_by_channel.get(ch_id, [])
        )
        channel_profiles[ch_id] = prof
        ch["primaryContentType"] = prof.primary_content_type
        ch["classificationConfidence"] = prof.confidence
        ch["classificationSource"] = prof.source

    classifier = ContentClassifier()
    for prof in channel_profiles.values():
        classifier.register_channel_profile(prof)

    tmdb_cache = {}
    tmdb_cache_file = Path("data/tmdb_poster_cache.json")
    if tmdb_cache_file.exists():
        try:
            tmdb_cache = json.loads(tmdb_cache_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    existing_programs = {}
    programs_file = Path("data/programs.json")
    if programs_file.exists():
        try:
            existing_programs = json.loads(programs_file.read_text(encoding="utf-8"))
        except Exception:
            pass

    programs_catalog = {}
    minimized_schedules = []

    for s in merged_schedules:
        title = s.get("title", "").strip()
        if not title:
            continue
        ch_id = s.get("channelId")
        ch_info = catalog_by_id.get(ch_id, {})
        ch_name = s.get("channelName") or ch_info.get("name_ar") or f"Channel {ch_id}"

        cls_res = classifier.classify(
            title=title,
            title_en=s.get("title_en"),
            source_program_type=s.get("programType"),
            category=s.get("category"),
            genre=s.get("genre"),
            overview=s.get("overview"),
            channel_id=ch_id,
            channel_name=ch_name,
            source_program_id=s.get("programId")
        )

        canonical_type = cls_res.content_type
        stable_id = cls_res.stable_program_id

        if title not in programs_catalog:
            meta = {
                "programId": stable_id,
                "title": title,
                "title_en": s.get("title_en"),
                "programType": canonical_type,
                "classificationConfidence": round(cls_res.confidence, 3),
                "classificationSource": cls_res.source,
                "priority": CONTENT_PRIORITY.get(canonical_type, 4)
            }
            poster = s.get("poster")
            if not poster or str(poster).startswith("data:"):
                cache_item = tmdb_cache.get(title)
                if isinstance(cache_item, dict) and cache_item.get("poster"):
                    poster = cache_item["poster"]
                elif title in existing_programs and existing_programs[title].get("poster"):
                    poster = existing_programs[title]["poster"]

            if poster and not str(poster).startswith("data:"):
                meta["poster"] = poster
            if s.get("overview"):
                meta["overview"] = s.get("overview")
            if s.get("rating") and s.get("rating") != "7.5":
                meta["rating"] = s.get("rating")
            if s.get("cast"):
                meta["cast"] = [
                    {"name": c.get("name", "").strip(), "character": c.get("character")}
                    for c in s.get("cast")
                    if isinstance(c, dict) and c.get("name")
                ]
            programs_catalog[title] = meta

        min_item = {
            "channelId": ch_id,
            "programId": stable_id,
            "title": title,
            "date": s.get("date"),
            "startTime": s.get("startTime"),
            "endTime": s.get("endTime"),
            "programType": canonical_type
        }
        if s.get("title_en"):
            min_item["title_en"] = s.get("title_en")

        minimized_schedules.append(min_item)

    dates = sorted(set(s.get("date") for s in minimized_schedules if s.get("date")))
    channels_count = len(set(s.get("channelId") for s in minimized_schedules if s.get("channelId")))

    # Version handling
    metadata_file = Path("data/metadata.json")
    prev_version = 100
    if metadata_file.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                old_m = json.load(f)
                prev_version = int(old_m.get("version", 100))
        except Exception:
            pass
    curr_version = prev_version + 1

    # Generate Delta
    from scripts.generate_delta import generate_delta
    prev_schedules_file = Path("data/schedules_prev.json")
    prev_schedules = []
    if prev_schedules_file.exists():
        try:
            with open(prev_schedules_file, "r", encoding="utf-8") as f:
                prev_schedules = json.load(f)
        except Exception:
            pass

    active_channel_dates = set((it.get("channelId"), it.get("date")) for it in fresh_items if it.get("channelId") and it.get("date"))
    delta = generate_delta(prev_schedules, minimized_schedules, prev_version, curr_version, active_channel_dates=active_channel_dates)
    deltas_dir = Path("data/deltas")
    deltas_dir.mkdir(parents=True, exist_ok=True)
    delta_filename = f"delta_{prev_version}_to_{curr_version}.json"
    delta_path = deltas_dir / delta_filename
    delta_path.write_text(json.dumps(delta, ensure_ascii=False, indent=2), encoding="utf-8")

    metadata = {
        "version": curr_version,
        "previousVersion": prev_version,
        "generatedAt": cairo_now_iso,
        "generatedAtUtc": utc_now_iso,
        "timezone": "Africa/Cairo",
        "dateRange": {
            "min": dates[0] if dates else None,
            "max": dates[-1] if dates else None,
            "totalDays": len(dates)
        },
        "channelsCount": channels_count,
        "broadcastsCount": len(minimized_schedules),
        "uniqueProgramsCount": len(programs_catalog),
        "delta": {
            "availableFrom": prev_version,
            "filename": delta_filename,
            "url": f"https://raw.githubusercontent.com/khalidfigo43/tv-guide-releases/main/data/deltas/{delta_filename}",
            "addedCount": delta["summary"]["addedCount"],
            "updatedCount": delta["summary"]["updatedCount"],
            "deletedCount": delta["summary"]["deletedCount"]
        },
        "mergeStats": merge_stats,
        "collectors": collector_reports,
        "validation": {
            "passed": True,
            "warnings": validation_res["warnings"]
        }
    }

    # 7. Write data files (pure JSON array for schedules.json, separate metadata.json)
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    assets_dir = Path("android/app/src/main/assets")
    assets_dir.mkdir(parents=True, exist_ok=True)

    json_content = json.dumps(minimized_schedules, ensure_ascii=False)
    programs_content = json.dumps(programs_catalog, ensure_ascii=False)
    meta_content = json.dumps(metadata, ensure_ascii=False, indent=2)
    channels_content = json.dumps(ALL_CHANNELS_CATALOG, ensure_ascii=False, indent=2)

    (data_dir / "schedules.json").write_text(json_content, encoding="utf-8")
    (data_dir / "programs.json").write_text(programs_content, encoding="utf-8")
    (data_dir / "metadata.json").write_text(meta_content, encoding="utf-8")
    (data_dir / "channels.json").write_text(channels_content, encoding="utf-8")
    (data_dir / "schedules_prev.json").write_text(json_content, encoding="utf-8")

    (assets_dir / "schedules.json").write_text(json_content, encoding="utf-8")
    (assets_dir / "programs.json").write_text(programs_content, encoding="utf-8")
    (assets_dir / "metadata.json").write_text(meta_content, encoding="utf-8")
    (assets_dir / "channels.json").write_text(channels_content, encoding="utf-8")

    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print(f"🎉 PIPELINE EXECUTION COMPLETED IN {elapsed:.1f}s")
    print("=" * 80)
    print(f"Total Broadcasts   : {len(merged_schedules):,}")
    print(f"Channels with Data : {channels_count}")
    print(f"Date Range         : {metadata['dateRange']['min']} -> {metadata['dateRange']['max']} ({metadata['dateRange']['totalDays']} days)")
    print(f"Saved Files        : data/schedules.json, data/metadata.json, assets/schedules.json")

    # Output GitHub Actions summary markdown if GITHUB_STEP_SUMMARY is set
    step_summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if step_summary_path:
        try:
            with open(step_summary_path, "a", encoding="utf-8") as f:
                f.write(f"## 📺 Daily TV Guide Sync Report ({today_str} Africa/Cairo)\n\n")
                f.write(f"- **Generated At**: `{cairo_now_iso}` (UTC: `{utc_now_iso}`)\n")
                f.write(f"- **Date Range**: `{metadata['dateRange']['min']}` to `{metadata['dateRange']['max']}` ({metadata['dateRange']['totalDays']} days)\n")
                f.write(f"- **Total Broadcasts**: **{len(merged_schedules):,}** across **{channels_count}** channels\n")
                f.write(f"- **New Broadcasts Added**: {merge_stats['inserted']:,}\n")
                f.write(f"- **Broadcasts Updated**: {merge_stats['updated']:,}\n")
                f.write(f"- **Retained Future Broadcasts**: {merge_stats['retained_future']:,}\n")
                f.write(f"- **Pruned Past Broadcasts**: {merge_stats['pruned_past']:,}\n\n")
                f.write("### 📡 Collectors Performance\n\n")
                f.write("| Collector | Status | Channels | Broadcasts | Date Range |\n")
                f.write("|:---|:---:|:---:|:---:|:---:|\n")
                for c_key, c_info in collector_reports.items():
                    f.write(f"| **{c_info.get('name')}** | `{c_info.get('status')}` | {c_info.get('channels_succeeded')}/{c_info.get('channels_attempted')} | {c_info.get('broadcasts_count'):,} | {c_info.get('min_date')} → {c_info.get('max_date')} |\n")
        except Exception as e:
            print(f"Warning writing GITHUB_STEP_SUMMARY: {e}")


if __name__ == "__main__":
    main()


