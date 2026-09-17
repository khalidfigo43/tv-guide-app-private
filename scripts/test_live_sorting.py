import sqlite3
from datetime import datetime

conn = sqlite3.connect("android/app/src/main/assets/tvguide_preloaded.db")
c = conn.cursor()

# Get today's date and current Cairo time
today = "2026-09-03"
now_time = "02:15"

c.execute("""
    SELECT s.channel_id, s.start_time, s.end_time, s.title, s.program_type
    FROM schedules s
    WHERE s.date = ? AND s.start_time <= ? AND (s.end_time > ? OR s.end_time < s.start_time)
""", (today, now_time, now_time))

rows = c.fetchall()
print(f"Total live now broadcasts found at {now_time}: {len(rows)}")

# Channel categories
MOVIE_CHANNELS = {1, 2, 3, 4, 11, 12, 13, 14, 62, 63, 64, 119, 10225, 10301, 15666, 15669}
SERIES_CHANNELS = {15, 30, 32, 36, 43, 60, 61, 65, 114}
CARTOON_CHANNELS = {17, 70, 71, 72, 73, 74}

def get_tier(cid, title, ptype):
    t = (ptype or "").lower()
    tit = (title or "").lower()
    
    # 1. Negative rules for news/sports/prayers
    if any(w in tit for w in ["أخبار", "اخبار", "نشرة", "نشره", "موجز", "مباراة", "مباراه", "الدوري", "كأس", "قرآن", "اذان", "صلاة", "صباح الخير"]):
        return 4
        
    # 2. Explicit keywords
    if "فيلم" in tit or "movie" in tit or cid in MOVIE_CHANNELS or t == "movie":
        return 1
    if "مسلسل" in tit or "series" in tit or cid in SERIES_CHANNELS or t == "series":
        return 2
    if "كارتون" in tit or "كرتون" in tit or "cartoon" in tit or "أنيمي" in tit or "انمي" in tit or cid in CARTOON_CHANNELS or t in ("cartoon", "kids"):
        return 3
    if t == "other":
        return 4
    return 4

tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
for r in rows:
    tier = get_tier(r[0], r[3], r[4])
    tier_counts[tier] += 1

print("Tier distribution for Live Now:")
print(f"  Tier 1 (Movies)  : {tier_counts[1]}")
print(f"  Tier 2 (Series)  : {tier_counts[2]}")
print(f"  Tier 3 (Cartoons): {tier_counts[3]}")
print(f"  Tier 4 (Other)   : {tier_counts[4]}")

conn.close()

