import sqlite3
import json

print("=" * 80)
print("INSPECTING USER ISSUES")
print("=" * 80)

# 1. Inspect Padel time channel
channels = json.load(open("data/channels.json", encoding="utf-8"))
padel_channels = [ch for ch in channels if "padel" in str(ch).lower() or "بادل" in str(ch)]
print("Padel channels in channels.json:", padel_channels)

# 2. Inspect channel with "ميلرز غيرل" and "هاري بوتر"
conn = sqlite3.connect("android/app/src/main/assets/tvguide_preloaded.db")
c = conn.cursor()

c.execute("SELECT channel_id, date, start_time, title FROM schedules WHERE title LIKE '%ميلرز%' OR title LIKE '%هاري بوتر%' LIMIT 10")
rows = c.fetchall()
print("\nSchedules with ميلرز / هاري بوتر:")
for r in rows:
    cid = r[0]
    ch = next((x for x in channels if x["id"] == cid), None)
    print(f"  ChID {cid}: {r[3]} ({r[1]} {r[2]}) -> Channel info: {ch}")

# 3. Check all channel IDs in schedules that are NOT in channels.json!
c.execute("SELECT DISTINCT channel_id FROM schedules")
all_sched_cids = [r[0] for r in c.fetchall()]
missing_cids = [cid for cid in all_sched_cids if not any(x["id"] == cid for x in channels)]
print(f"\nMissing channel IDs in schedules that don't exist in channels.json: {missing_cids}")
for cid in missing_cids:
    c.execute("SELECT title, date, start_time FROM schedules WHERE channel_id = ? LIMIT 5", (cid,))
    print(f"  Missing CID {cid} samples:", c.fetchall())

# 5. Inspect Channel 21 (القناة الأولى المصرية)
c.execute("SELECT date, start_time, title, program_type FROM schedules WHERE channel_id = 21 LIMIT 25")
print("\nChannel 21 samples:")
for r in c.fetchall():
    print(f"  {r[0]} {r[1]}: \"{r[2]}\" ({r[3]})")

# 6. Inspect ON E (Channel 31) titles
c.execute("SELECT date, start_time, title, program_type FROM schedules WHERE channel_id = 31 AND title LIKE '%عربي%' LIMIT 10")
print("\nON E (Ch 31) 'عربي' samples:")
for r in c.fetchall():
    print(f"  {r[0]} {r[1]}: \"{r[2]}\" ({r[3]})")

# 8. Deep inspect 'عربي' on ON E and CBC
c.execute("SELECT s.channel_id, s.date, s.start_time, s.end_time, s.title, s.title_en, s.program_id FROM schedules s WHERE s.title = 'عربي'")
print("\nDetailed 'عربي' rows:")
for r in c.fetchall():
    ch = next((x for x in channels if x["id"] == r[0]), None)
    cname = ch.get("displayName") or ch.get("name_ar") if ch else f"Ch {r[0]}"
    print(f"  {cname} ({r[0]}): {r[1]} {r[2]} -> {r[3]}, title_en: {r[5]}, pid: {r[6]}")

# 9. Check what ElCinema had for these times
conn.close()
