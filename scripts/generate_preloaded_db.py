import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

# Insert parent dir to import collectors if needed
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

DATA_DIR = Path("data")
ASSETS_DIR = Path("android/app/src/main/assets")
DB_PATH = ASSETS_DIR / "tvguide_preloaded.db"


def clean_title(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"^(مسلسل|فيلم|مسرحية|برنامج|كرتون|أنيمي|سلسلة|عرض)\s+", "", s.strip())
    s = re.sub(r"\s+ج\s*\d+", "", s)
    s = re.sub(r"\s+الجزء\s+.*", "", s)
    s = re.sub(r"\s+الموسم\s+.*", "", s)
    s = re.sub(r"\s+s\d+.*", "", s, flags=re.IGNORECASE)
    return s.strip()


def normalize_arabic(text: str) -> str:
    if not text:
        return ""
    s = clean_title(text)
    s = re.sub(r"[\u064B-\u065F\u0670]", "", s)
    s = re.sub(r"[أإآٱ]", "ا", s)
    s = s.replace("ة", "ه").replace("ى", "ي")
    s = re.sub(r"[^\w\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


DELETED_CHANNEL_IDS = {91, 179, 196, 200, 203, 204, 216, 217, 234, 235, 236, 238, 239, 240, 241}

NON_FICTION_KEYWORDS = [
    'أخبار', 'اخبار', 'نشرة', 'نشره', 'موجز', 'مباراة', 'مباراه', 'الدوري', 'كأس', 'كاس', 'بطولة', 'بطوله',
    'كرة القدم', 'كرة السلة', 'رياضة', 'رياضه', 'قرآن', 'قران', 'أذان', 'اذان', 'صلاة', 'صلاه', 'حديث الروح',
    'تلاوة', 'تلاوه', 'صباح الخير', 'صباح الورد', 'صباحك', 'أحلى أكلة', 'مطبخ', 'الشيف', 'برامج', 'بث ليلي',
    '90 دقيقة', 'الحكاية', 'معكم منى الشاذلي', 'كل يوم', 'مساء dmc', 'يحدث في مصر', 'على مسئوليتي', 'كلمة أخيرة',
    'حفل', 'حفلة', 'طرب', 'سهرة مع', 'استوديو', 'تلفزيون', 'news', 'نيوز', 'إذاعة', 'اذاعة', 'راديو', 'radio',
    'قناة', 'بث مباشر', 'أخبار العالم', 'نشرة الأخبار', 'موجز الأخبار', 'اخبار الحدث', 'الحياة اليوم',
    'التاسعة', 'التاسعه', 'عرب وود', 'بيزنيس', 'فريفايد', 'business'
]

MOVIE_CHANNELS = {1, 2, 3, 4, 11, 12, 13, 14, 62, 63, 64, 119, 10225, 10301, 15666, 15669}
SERIES_CHANNELS = {15, 30, 32, 36, 43, 60, 61, 65, 114}
CARTOON_CHANNELS = {17, 70, 71, 72, 73, 74}


def is_blacklisted_channel(ch_id: int | None, name: str) -> bool:
    if ch_id in DELETED_CHANNEL_IDS:
        return True
    if not name:
        return False
    n = name.lower().strip()
    return "esports" in n or "e-sports" in n or "gametoon" in n or \
           "kapatid" in n or "rfm tv" in n or "mcm top" in n or "dzmm" in n or \
           "teleradyo" in n or "mor global" in n or "rt english" in n or \
           "rt arabic" in n or "روسيا اليوم" in n or "cinemo" in n or \
           "gma pinoy" in n or "gma life" in n or "padel" in n or n == "anc" or \
           "stv1" in n or "stv 1" in n or "تلفزيون البحرين" in n or "bahrain tv" in n


def is_esports_channel(name: str) -> bool:
    return is_blacklisted_channel(None, name)


def main():
    print("=" * 80)
    print("GENERATING OPTIMIZED PRELOADED SQLITE DATABASE WITH FULL POSTERS COVERAGE")
    print("=" * 80)

    sched_file = DATA_DIR / "schedules.json"
    prog_file = DATA_DIR / "programs.json"
    chan_file = DATA_DIR / "channels.json"

    if not sched_file.exists() or not prog_file.exists():
        print("❌ Error: Missing data/schedules.json or data/programs.json")
        sys.exit(1)

    t0 = time.perf_counter()

    # 1. Load source JSONs
    print("Loading source files...")
    sched_data = json.loads(sched_file.read_text(encoding="utf-8"))
    schedules = sched_data.get("schedules", []) if isinstance(sched_data, dict) else sched_data
    programs = json.loads(prog_file.read_text(encoding="utf-8"))
    channels = json.loads(chan_file.read_text(encoding="utf-8")) if chan_file.exists() else []

    channel_map = {ch["id"]: ch for ch in channels}
    paid_channel_ids = {ch["id"] for ch in channels if ch.get("is_paid", False) or ch.get("is_paid_channel", False)}

    print(f"Loaded: {len(schedules)} schedules, {len(programs)} programs, {len(channels)} channels")

    # 2. Extract poster cache from git history and enriched_content
    print("Extracting high-resolution posters from git history and TMDB enriched_content...")
    title_to_poster = {}
    norm_to_poster = {}

    try:
        cmd = ["git", "show", "4c2948c:android/app/src/main/assets/schedules.json"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode == 0:
            git_scheds = json.loads(proc.stdout.decode("utf-8"))
            for x in git_scheds:
                t = x.get("title")
                p = x.get("poster")
                if t and p and not str(p).startswith("data:"):
                    title_to_poster[t.strip()] = p
                    norm_to_poster[normalize_arabic(t)] = p
            print(f"  ✓ Loaded {len(git_scheds)} historical schedules from git, extracted {len(title_to_poster)} posters")
    except Exception as e:
        print("  ⚠️ Git extraction warning:", e)

    ec_file = DATA_DIR / "enriched_content.json"
    if ec_file.exists():
        try:
            ec = json.loads(ec_file.read_text(encoding="utf-8"))
            for v in ec.values():
                t_ar = v.get("title_ar")
                s_t = v.get("source_title")
                p_path = v.get("poster_path")
                if p_path:
                    url = p_path if p_path.startswith("http") else f"https://image.tmdb.org/t/p/w500{p_path}"
                    if t_ar:
                        title_to_poster[t_ar.strip()] = url
                        norm_to_poster[normalize_arabic(t_ar)] = url
                    if s_t:
                        title_to_poster[s_t.strip()] = url
                        norm_to_poster[normalize_arabic(s_t)] = url
            print(f"  ✓ Loaded TMDB matches from enriched_content.json")
        except Exception as e:
            print("  ⚠️ Enriched content extraction warning:", e)

    title_to_meta = {}
    norm_to_meta = {}
    cache_file = DATA_DIR / "tmdb_poster_cache.json"
    if cache_file.exists():
        try:
            t_cache = json.loads(cache_file.read_text(encoding="utf-8"))
            for t_key, val in t_cache.items():
                if val and isinstance(val, dict):
                    t_clean = t_key.strip()
                    title_to_meta[t_clean] = val
                    norm_to_meta[normalize_arabic(t_clean)] = val
                    if val.get("poster"):
                        url = val["poster"]
                        title_to_poster[t_clean] = url
                        norm_to_poster[normalize_arabic(t_clean)] = url
            print(f"  ✓ Loaded TMDB cache from tmdb_poster_cache.json ({len(title_to_meta)} entries)")
        except Exception as e:
            print("  ⚠️ TMDB cache warning:", e)

    print(f"Total poster mappings ready: {len(title_to_poster)} exact, {len(norm_to_poster)} normalized")

    def get_meta_for_title(t: str) -> dict | None:
        if not t:
            return None
        t_clean = t.strip()
        return title_to_meta.get(t_clean) or norm_to_meta.get(normalize_arabic(t_clean))

    def get_poster_for_title(t: str) -> str | None:
        if not t:
            return None
        t_clean = t.strip()
        return title_to_poster.get(t_clean) or norm_to_poster.get(normalize_arabic(t_clean))

    # Remove existing DB file
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("PRAGMA journal_mode = OFF")
    c.execute("PRAGMA synchronous = OFF")

    # 3. Create tables
    print("Creating SQLite tables and indexes...")
    c.execute("""
    CREATE TABLE schedules (
        channel_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        program_id TEXT,
        title TEXT NOT NULL,
        title_en TEXT,
        program_type TEXT,
        PRIMARY KEY (channel_id, date, start_time)
    )
    """)
    c.execute("CREATE INDEX idx_sched_ch_date ON schedules(channel_id, date)")
    c.execute("CREATE INDEX idx_sched_date_time ON schedules(date, start_time)")
    c.execute("CREATE INDEX idx_sched_program_id ON schedules(program_id)")
    c.execute("CREATE INDEX idx_sched_title ON schedules(title)")

    c.execute("""
    CREATE TABLE programs (
        program_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        title_en TEXT,
        program_type TEXT NOT NULL,
        priority INTEGER DEFAULT 4,
        poster TEXT,
        overview TEXT,
        rating TEXT,
        cast_json TEXT
    )
    """)
    c.execute("CREATE INDEX idx_prog_title ON programs(title)")
    c.execute("CREATE INDEX idx_prog_type ON programs(program_type)")

    c.execute("""
    CREATE TABLE shows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_id TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        title_en TEXT,
        program_type TEXT NOT NULL,
        priority_tier INTEGER NOT NULL,
        poster TEXT,
        overview TEXT,
        rating TEXT,
        cast_json TEXT,
        airings_count INTEGER DEFAULT 0,
        nearest_date TEXT,
        nearest_time TEXT,
        nearest_channel_name TEXT,
        nearest_channel_id INTEGER,
        has_free_airings INTEGER DEFAULT 1,
        is_paid_only INTEGER DEFAULT 0,
        title_norm TEXT,
        title_en_norm TEXT,
        channel_norm TEXT,
        cast_norm TEXT
    )
    """)
    c.execute("CREATE INDEX idx_shows_category ON shows(program_type, priority_tier)")
    c.execute("CREATE INDEX idx_shows_priority ON shows(priority_tier, airings_count DESC)")
    c.execute("CREATE INDEX idx_shows_title_norm ON shows(title_norm)")
    c.execute("CREATE INDEX idx_shows_program_id ON shows(program_id)")

    c.execute("""
    CREATE TABLE sync_meta (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    # 4. Populate schedules
    print("Populating schedules...")

    # Collect all channel names to identify channel placeholders
    all_channel_names = set()
    for ch in channels:
        for k in ["name", "name_ar", "name_en", "displayName", "nameAr"]:
            v = ch.get(k)
            if v and isinstance(v, str) and len(v.strip()) > 1:
                all_channel_names.add(v.strip().lower())
                all_channel_names.add(normalize_arabic(v.strip()))

    GENERIC_WORDS_FORBIDDEN_AS_MOVIE = {
        "الراي", "العربية", "الحدث", "الأخبار", "الاخبار", "المستقبل", "الشروق", "النهار", "الوطن",
        "تلفزيوني", "منوعات", "اف دي ال", "myx", "ktv 1", "ktv", "bloomberg originals", "وثائقي",
        "تلفزيون السعودية", "تلفزيون البحرين", "بي بي سي نيوز", "bbc news"
    }

    def classify_show(title_text: str, title_en_text: str | None, channel_id: int | None, initial_type: str | None):
        t_lower = (initial_type or "").lower()
        tit_lower = title_text.lower().strip()
        tit_norm = normalize_arabic(title_text)

        # 0. Channel Placeholder or Generic Word check -> NEVER a movie or series
        if tit_lower in GENERIC_WORDS_FORBIDDEN_AS_MOVIE or tit_norm in GENERIC_WORDS_FORBIDDEN_AS_MOVIE:
            return "other", 4
        if (tit_lower in all_channel_names or tit_norm in all_channel_names) and not tit_lower.startswith("مسلسل") and not tit_lower.startswith("فيلم"):
            return "other", 4
        if re.search(r'\bhd\b', tit_lower) or any(tit_lower.startswith(b) for b in ['mbc ', 'ام بي سي ', 'إم بي سي ', 'alfa ', 'ألفا ', 'rotana ', 'روتانا ', 'osn ', 'أو إس إن ']):
            if not tit_lower.startswith("مسلسل") and not tit_lower.startswith("فيلم"):
                return "other", 4

        # 1. Negative keywords for non-fiction (News, Sports, Religion, Talk shows)
        if any(kw in tit_lower for kw in NON_FICTION_KEYWORDS) and not tit_lower.startswith("مسلسل") and "فيلم" not in tit_lower and not tit_lower.startswith("رافت"):
            return "other", 4

        # 2. TMDB metadata check (now safe because negative keywords and placeholders were filtered first!)
        meta = get_meta_for_title(title_text)
        if meta:
            if meta.get("media_type") == "movie":
                return "movie", 1
            if meta.get("media_type") == "tv":
                return "series", 2

        # 3. Explicit Title keywords
        if "فيلم" in tit_lower or "movie" in tit_lower or (channel_id and channel_id in MOVIE_CHANNELS):
            return "movie", 1
            
        if "مسلسل" in tit_lower or "series" in tit_lower or (channel_id and channel_id in SERIES_CHANNELS) or any(f"ج{i}" in tit_lower for i in range(1, 10)):
            return "series", 2
            
        if "كارتون" in tit_lower or "كرتون" in tit_lower or "cartoon" in tit_lower or (channel_id and channel_id in CARTOON_CHANNELS) or t_lower in ("cartoon", "kids", "animation"):
            return "cartoon", 3

        # 4. Source initial_type fallback
        if t_lower in ("movie", "film"):
            return "movie", 1
        if t_lower in ("series", "drama"):
            return "series", 2
            
        return "other", 4

    import hashlib
    title_to_pid = {v.get("title", k).strip(): v.get("programId", k) for k, v in programs.items()}
    for s in schedules:
        stitle = s.get("title", "").strip()
        if stitle and stitle not in title_to_pid:
            pid = f"prog_{hashlib.md5(stitle.encode('utf-8')).hexdigest()[:12]}"
            title_to_pid[stitle] = pid
            programs[pid] = {
                "programId": pid,
                "title": stitle,
                "title_en": s.get("title_en"),
                "programType": s.get("programType", "other"),
                "poster": get_poster_for_title(stitle)
            }

    s_rows = []
    for s in schedules:
        ch_id = s.get("channelId")
        ch_name = s.get("channelName", "")
        title = s.get("title", "")
        if not ch_id or not title or is_blacklisted_channel(ch_id, ch_name) or is_blacklisted_channel(None, title):
            continue
        pid = title_to_pid.get(title.strip()) or s.get("programId") or ""
        s_type, _ = classify_show(title, s.get("title_en"), ch_id, s.get("programType"))
        s_rows.append((
            ch_id,
            s.get("date", ""),
            s.get("startTime", ""),
            s.get("endTime"),
            pid,
            title,
            s.get("title_en"),
            s_type
        ))
    c.executemany("INSERT OR REPLACE INTO schedules VALUES (?, ?, ?, ?, ?, ?, ?, ?)", s_rows)

    # 5. Populate programs (with enriched posters!)
    print("Populating programs with posters...")
    p_rows = []
    updated_programs = {}
    posters_count = 0
    for k, v in programs.items():
        title = v.get("title", k)
        pid = v.get("programId", k)
        ptype, priority = classify_show(title, v.get("title_en"), None, v.get("programType"))
        cast = v.get("cast")
        cast_json = json.dumps(cast, ensure_ascii=False) if cast else None

        meta = get_meta_for_title(title)
        poster = v.get("poster") or get_poster_for_title(title)
        overview = v.get("overview") or (meta.get("overview") if meta else None)
        rating = v.get("rating") or (meta.get("rating") if meta else "7.5") or "7.5"

        if poster:
            posters_count += 1
            v["poster"] = poster
        if overview:
            v["overview"] = overview
        v["rating"] = rating

        v["programType"] = ptype
        v["priority"] = priority
        updated_programs[k] = v

        p_rows.append((
            pid,
            title,
            v.get("title_en"),
            ptype,
            priority,
            poster,
            overview,
            rating,
            cast_json
        ))
    c.executemany("INSERT OR REPLACE INTO programs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", p_rows)
    print(f"  ✓ Programs populated: {len(p_rows)} rows ({posters_count} have posters)")

    # Save updated programs to json files
    prog_file.write_text(json.dumps(updated_programs, ensure_ascii=False, indent=2), encoding="utf-8")
    (ASSETS_DIR / "programs.json").write_text(json.dumps(updated_programs, ensure_ascii=False, indent=2), encoding="utf-8")

    # 6. Populate derived shows catalog (with enriched posters!)
    print("Pre-aggregating derived shows catalog...")
    c.execute("""
    SELECT 
        program_id,
        COUNT(*) as airings_count,
        MIN(date || ' ' || start_time) as first_dt,
        MIN(channel_id) as sample_ch
    FROM schedules
    WHERE program_id IS NOT NULL AND program_id != ''
    GROUP BY program_id
    """)
    sched_stats = {r[0]: (r[1], r[2], r[3]) for r in c.fetchall()}

    shows_rows = []
    for p in p_rows:
        pid = p[0]
        title = p[1]
        title_en = p[2] or ""
        ptype = p[3]
        priority = p[4]
        poster = p[5]
        overview = p[6]
        rating = p[7]
        cast_json = p[8]

        stats = sched_stats.get(pid, (0, "", 0))
        airings_count = stats[0]
        if airings_count == 0:
            continue
        first_dt = stats[1]
        nearest_ch_id = stats[2]

        nearest_date = first_dt[:10] if len(first_dt) >= 10 else ""
        nearest_time = first_dt[11:16] if len(first_dt) >= 16 else ""

        ch = channel_map.get(nearest_ch_id, {})
        nearest_channel_name = ch.get("displayName") or ch.get("name_ar") or ch.get("nameAr") or ch.get("name") or ch.get("name_en") or "قناة"

        is_paid_only = 1 if nearest_ch_id in paid_channel_ids else 0
        has_free = 0 if is_paid_only else 1

        title_norm = normalize_arabic(title)
        title_en_norm = normalize_arabic(title_en)
        channel_norm = normalize_arabic(nearest_channel_name)

        cast_names = []
        if cast_json:
            try:
                for cm in json.loads(cast_json):
                    if isinstance(cm, dict) and "name" in cm:
                        cast_names.append(normalize_arabic(cm["name"]))
            except Exception:
                pass
        cast_norm = " ".join(cast_names)

        shows_rows.append((
            pid,
            title,
            title_en,
            ptype,
            priority,
            poster,
            overview,
            rating,
            cast_json,
            airings_count,
            nearest_date,
            nearest_time,
            nearest_channel_name,
            nearest_ch_id,
            has_free,
            is_paid_only,
            title_norm,
            title_en_norm,
            channel_norm,
            cast_norm
        ))

    c.executemany("""
    INSERT OR REPLACE INTO shows (
        program_id, title, title_en, program_type, priority_tier, poster, overview, rating, cast_json,
        airings_count, nearest_date, nearest_time, nearest_channel_name, nearest_channel_id,
        has_free_airings, is_paid_only, title_norm, title_en_norm, channel_norm, cast_norm
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, shows_rows)

    # 7. Metadata version
    meta_ver = "105"
    meta_path = DATA_DIR / "metadata.json"
    if meta_path.exists():
        try:
            m_obj = json.loads(meta_path.read_text(encoding="utf-8"))
            meta_ver = str(m_obj.get("version", 105))
        except Exception:
            pass
    c.execute("INSERT OR REPLACE INTO sync_meta VALUES ('version', ?)", (meta_ver,))

    conn.commit()
    c.execute("VACUUM")
    conn.close()

    elapsed = time.perf_counter() - t0
    file_size_mb = DB_PATH.stat().st_size / (1024 * 1024)

    print(f"✓ Generated {DB_PATH} in {elapsed:.2f}s ({file_size_mb:.2f} MB)")
    print("Database verification:")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print("  schedules count :", c.execute("SELECT COUNT(*) FROM schedules").fetchone()[0])
    print("  programs count  :", c.execute("SELECT COUNT(*) FROM programs").fetchone()[0])
    print("  programs with poster:", c.execute("SELECT COUNT(*) FROM programs WHERE poster IS NOT NULL").fetchone()[0])
    print("  shows count     :", c.execute("SELECT COUNT(*) FROM shows").fetchone()[0])
    print("  shows with poster   :", c.execute("SELECT COUNT(*) FROM shows WHERE poster IS NOT NULL").fetchone()[0])
    conn.close()
    print("=" * 80)


if __name__ == "__main__":
    main()
