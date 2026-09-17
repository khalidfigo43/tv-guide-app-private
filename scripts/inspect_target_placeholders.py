import sqlite3, json

conn = sqlite3.connect("android/app/src/main/assets/tvguide_preloaded.db")
c = conn.cursor()

target_cids = [21, 27, 31, 48, 50, 61, 154]
channels = json.load(open("data/channels.json", encoding="utf-8"))

for cid in target_cids:
    ch = next((x for x in channels if x["id"] == cid), None)
    cname = ch.get("displayName") or ch.get("name_ar") if ch else f"Ch {cid}"
    print(f"\n{'='*30}\nChannel {cid}: {cname}\n{'='*30}")
    c.execute("""
        SELECT date, start_time, end_time, title, program_type 
        FROM schedules 
        WHERE channel_id = ? AND (title LIKE '%برنامج ت%' OR title = 'عربي' OR title = 'رقم 10')
        ORDER BY date, start_time
        LIMIT 15
    """, (cid,))
    for r in c.fetchall():
        print(f"  {r[0]} {r[1]}-{r[2]}: '{r[3]}' ({r[4]})")

conn.close()
