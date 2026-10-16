import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import zoneinfo
    cairo_tz = zoneinfo.ZoneInfo("Africa/Cairo")
except Exception:
    import pytz
    cairo_tz = pytz.timezone("Africa/Cairo")

trigger_event = sys.argv[1] if len(sys.argv) > 1 else "manual"
cairo_now = datetime.now(cairo_tz)
print(f"[*] Current Africa/Cairo Time: {cairo_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

# Verify if today's sync has already been generated
already_ran_today = False
metadata_path = Path("data/metadata.json")
if metadata_path.exists():
    try:
        import json
        meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        gen_at = str(meta.get("generatedAt", ""))
        today_date_str = cairo_now.strftime("%Y-%m-%d")
        if gen_at.startswith(today_date_str):
            already_ran_today = True
    except Exception:
        pass

should_run = "true"
if trigger_event == "schedule":
    if already_ran_today:
        print(f"[Wf] Sync already executed successfully today ({cairo_now.strftime('%Y-%m-%d')}). Skipping duplicate run.")
        should_run = "false"
    elif cairo_now.hour in (0, 1, 2):
        print(f"[+] Africa/Cairo hour is {cairo_now.hour} (within 00:00-02:59 window). Proceeding with scheduled sync.")
        should_run = "true"
    else:
        print(f"[Wf] Africa/Cairo hour is {cairo_now.hour} (outside midnight window). Skipping scheduled trigger.")
        should_run = "false"
else:
    print(f"[+] Trigger event is '{trigger_event}'. Proceeding immediately.")

github_output = os.getenv("GITHUB_OUTPUT")
if github_output:
    try:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"should_run={should_run}\n")
    except Exception as e:
        print(f"[!] Warning writing to GITHUB_OUTPUT: {e}")

sys.exit(0)
