import os
import sys
from datetime import datetime

try:
    import zoneinfo
    cairo_tz = zoneinfo.ZoneInfo("Africa/Cairo")
except Exception:
    import pytz
    cairo_tz = pytz.timezone("Africa/Cairo")

trigger_event = sys.argv[1] if len(sys.argv) > 1 else "manual"
cairo_now = datetime.now(cairo_tz)
print(f"[*] Current Africa/Cairo Time: {cairo_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

should_run = "true"
if trigger_event == "schedule":
    if cairo_now.hour != 0:
        print(f"[Wf] Africa/Cairo hour is {cairo_now.hour} (not midnight 00:00). Skipping scheduled trigger safely.")
        should_run = "false"
    else:
        print("[+] Africa/Cairo hour is 0 (midnight 00:00). Proceeding with scheduled sync.")
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
