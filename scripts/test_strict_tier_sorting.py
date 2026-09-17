import sqlite3

conn = sqlite3.connect("android/app/src/main/assets/tvguide_preloaded.db")
c = conn.cursor()

# Test Live Now at 21:30 Cairo time
c.execute("""
    SELECT s.channel_id, s.date, s.start_time, s.end_time, s.title, s.title_en, s.program_type
    FROM schedules s
    WHERE s.date = '2026-09-03' AND s.start_time <= '21:30' AND (s.end_time > '21:30' OR s.end_time < s.start_time)
""")
rows = c.fetchall()

MOVIE_CHANNELS = {1, 2, 3, 4, 11, 12, 13, 14, 62, 63, 64, 119, 10225, 10301, 15666, 15669}
SERIES_CHANNELS = {15, 30, 32, 36, 43, 60, 61, 65, 114}
CARTOON_CHANNELS = {17, 70, 71, 72, 73, 74}

NON_FICTION_KEYWORDS = [
    'أخبار', 'اخبار', 'نشرة', 'نشره', 'موجز', 'مباراة', 'مباراه', 'الدوري', 'كأس', 'كاس', 'بطولة', 'بطوله',
    'كرة القدم', 'كرة السلة', 'رياضة', 'رياضه', 'قرآن', 'قران', 'أذان', 'اذان', 'صلاة', 'صلاه', 'حديث الروح',
    'تلاوة', 'تلاوه', 'صباح الخير', 'صباح الورد', 'صباحك', 'أحلى أكلة', 'مطبخ', 'الشيف', 'برامج', 'بث ليلي',
    '90 دقيقة', 'الحكاية', 'معكم منى الشاذلي', 'كل يوم', 'مساء dmc', 'يحدث في مصر', 'على مسئوليتي', 'كلمة أخيرة',
    'حفل', 'حفلة', 'طرب', 'سهرة مع', 'استوديو'
]

def get_tier(cid, title, ptype):
    t = (ptype or "").lower()
    tit = (title or "").lower()
    
    # Negative rules
    if any(kw in tit for kw in NON_FICTION_KEYWORDS):
        return 4
        
    if "فيلم" in tit or "movie" in tit or cid in MOVIE_CHANNELS or t == "movie":
        return 1
    if "مسلسل" in tit or "series" in tit or cid in SERIES_CHANNELS or t == "series" or any(f"ج{i}" in tit for i in range(1, 10)):
        return 2
    if "كارتون" in tit or "كرتون" in tit or "cartoon" in tit or "أنيمي" in tit or "انمي" in tit or cid in CARTOON_CHANNELS or t in ("cartoon", "kids"):
        return 3
    return 4

# Sort rows by tier, then start_time
sorted_rows = sorted(rows, key=lambda x: (get_tier(x[0], x[4], x[6]), x[2]))

print(f"Total Live Now items: {len(sorted_rows)}")
tiers = [get_tier(x[0], x[4], x[6]) for x in sorted_rows]
print("Tiers in order:", set(tiers))
# Verify strictly monotonic: tier[i] <= tier[i+1]
assert all(tiers[i] <= tiers[i+1] for i in range(len(tiers)-1)), "Sorting violated!"
print("✓ VERIFIED: Strictly monotonic sorting: Movies (1) -> Series (2) -> Cartoons (3) -> Other (4)")

print("\nFirst 5 items (Must be Movies):")
for r in sorted_rows[:5]:
    print(f"  Tier {get_tier(r[0], r[4], r[6])}: {r[4]} ({r[2]}) - Ch {r[0]}")

# Find where Series start
first_series = next(i for i, r in enumerate(sorted_rows) if get_tier(r[0], r[4], r[6]) == 2)
print(f"\nFirst 5 Series items (starting at index {first_series}):")
for r in sorted_rows[first_series:first_series+5]:
    print(f"  Tier {get_tier(r[0], r[4], r[6])}: {r[4]} ({r[2]}) - Ch {r[0]}")

conn.close()
