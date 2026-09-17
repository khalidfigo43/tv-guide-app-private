"""
TV Guide - Incremental Delta Generator
Compares previous schedules snapshot against new schedules snapshot to generate
minimal, atomic deltas (added, updated, deleted) for lightweight Android synchronization.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Tuple


def normalize_pk(item: Dict[str, Any]) -> Tuple[int, str, str]:
    """Primary key for a broadcast: (channelId, date, startTime)."""
    ch_id = int(item.get("channelId") or 0)
    date_str = str(item.get("date") or "").strip()
    start_time = str(item.get("startTime") or "").strip()
    return (ch_id, date_str, start_time)


def generate_delta(
    prev_schedules: List[Dict[str, Any]],
    curr_schedules: List[Dict[str, Any]],
    prev_version: int,
    curr_version: int,
    active_channel_dates: Optional[Any] = None
) -> Dict[str, Any]:
    prev_map = {normalize_pk(s): s for s in prev_schedules if normalize_pk(s)[0] > 0}
    curr_map = {normalize_pk(s): s for s in curr_schedules if normalize_pk(s)[0] > 0}

    added = []
    updated = []
    deleted = []

    # 1. Check added & updated
    for pk, curr_item in curr_map.items():
        if pk not in prev_map:
            added.append(curr_item)
        else:
            prev_item = prev_map[pk]
            changed = False
            for field in ["title", "title_en", "endTime", "programType", "programId"]:
                if curr_item.get(field) != prev_item.get(field):
                    changed = True
                    break
            if changed:
                updated.append(curr_item)

    # 2. Check deleted (ONLY for dates that were actively refreshed, never unrefreshed future dates)
    for pk in prev_map:
        if pk not in curr_map:
            # If active_channel_dates specified, only delete if this (channelId, date) was actively refreshed
            if active_channel_dates is not None:
                if (pk[0], pk[1]) in active_channel_dates:
                    deleted.append({
                        "channelId": pk[0],
                        "date": pk[1],
                        "startTime": pk[2]
                    })
            else:
                deleted.append({
                    "channelId": pk[0],
                    "date": pk[1],
                    "startTime": pk[2]
                })

    # Sort for deterministic output
    added.sort(key=lambda x: (x.get("date", ""), x.get("startTime", ""), x.get("channelId", 0)))
    updated.sort(key=lambda x: (x.get("date", ""), x.get("startTime", ""), x.get("channelId", 0)))
    deleted.sort(key=lambda x: (x.get("date", ""), x.get("startTime", ""), x.get("channelId", 0)))

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "version": curr_version,
        "previousVersion": prev_version,
        "generatedAt": now_iso,
        "summary": {
            "addedCount": len(added),
            "updatedCount": len(updated),
            "deletedCount": len(deleted),
            "totalCurrent": len(curr_map)
        },
        "added": added,
        "updated": updated,
        "deleted": deleted
    }


def main():
    data_dir = Path("data")
    deltas_dir = data_dir / "deltas"
    deltas_dir.mkdir(parents=True, exist_ok=True)

    schedules_file = data_dir / "schedules.json"
    prev_schedules_file = data_dir / "schedules_prev.json"
    metadata_file = data_dir / "metadata.json"

    if not schedules_file.exists():
        print(f"Error: {schedules_file} does not exist.")
        sys.exit(1)

    with open(schedules_file, "r", encoding="utf-8") as f:
        curr_schedules = json.load(f)

    prev_version = 100
    if metadata_file.exists():
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
                prev_version = int(meta.get("version", 100))
        except Exception:
            pass

    curr_version = prev_version + 1

    if prev_schedules_file.exists():
        with open(prev_schedules_file, "r", encoding="utf-8") as f:
            prev_schedules = json.load(f)
    else:
        prev_schedules = []

    delta = generate_delta(prev_schedules, curr_schedules, prev_version, curr_version)
    delta_filename = f"delta_{prev_version}_to_{curr_version}.json"
    delta_file = deltas_dir / delta_filename

    delta_json = json.dumps(delta, ensure_ascii=False, indent=2)
    delta_file.write_text(delta_json, encoding="utf-8")

    print(f"[+] Generated Delta: {delta_filename}")
    print(f"    Added  : {delta['summary']['addedCount']:,}")
    print(f"    Updated: {delta['summary']['updatedCount']:,}")
    print(f"    Deleted: {delta['summary']['deletedCount']:,}")
    print(f"    Size   : {len(delta_json) / 1024:.1f} KB")

    with open(prev_schedules_file, "w", encoding="utf-8") as f:
        json.dump(curr_schedules, f, ensure_ascii=False)


if __name__ == "__main__":
    main()

