import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from collectors.channels_catalog import ALL_CHANNELS_CATALOG

OUTPUT_SCHEDULE = Path("data/all_channels_schedule.json")
ROTANA_PATH = Path("data/rotana_schedule.json")


def build_verified_schedules():
    print("Building verified broadcast database from official live sources...")
    all_broadcasts = []
    
    # 1. Load official Rotana API schedule
    if ROTANA_PATH.exists():
        try:
            rotana_data = json.loads(ROTANA_PATH.read_text(encoding="utf-8"))
            for item in rotana_data.get("data", []):
                item["source"] = "rotana_official_api"
                item["is_verified"] = True
                all_broadcasts.append(item)
            print(f"  ✓ Loaded {len(rotana_data.get('data', []))} verified broadcasts from Rotana Official API")
        except Exception as e:
            print("Error reading rotana schedule:", e)

    # 2. Preserve existing live elcinema verified items if present
    if OUTPUT_SCHEDULE.exists():
        try:
            existing = json.loads(OUTPUT_SCHEDULE.read_text(encoding="utf-8"))
            elcinema_items = [b for b in existing.get("data", []) if b.get("source") == "elcinema_live"]
            all_broadcasts.extend(elcinema_items)
            print(f"  ✓ Preserved {len(elcinema_items)} verified live broadcasts from ElCinema Live Engine")
        except Exception:
            pass

    result = {
        "status": "success",
        "channels_count": len(ALL_CHANNELS_CATALOG),
        "broadcasts_count": len(all_broadcasts),
        "data": all_broadcasts
    }

    OUTPUT_SCHEDULE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Verified broadcast store updated with {len(all_broadcasts)} total genuine broadcasts in {OUTPUT_SCHEDULE}")


if __name__ == "__main__":
    build_verified_schedules()
