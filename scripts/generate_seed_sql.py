import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from collectors.channels_catalog import ALL_CHANNELS_CATALOG

ENRICHED_FILE = Path("data/enriched_content.json")
SCHEDULE_FILE = Path("data/all_channels_schedule.json")
ROTANA_SCHEDULE_FILE = Path("data/rotana_schedule.json")
MANUAL_FILE = Path("data/manual_mappings.json")
OUTPUT_SQL = Path("supabase/seed.sql")


def normalize_title(title):
    if not title:
        return ""
    text = str(title).lower().strip()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    replacements = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    arabic_digits = {"٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4", "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9"}
    for old, new in arabic_digits.items():
        text = text.replace(old, new)
    text = text.replace("ـ", "")
    text = re.sub(r"[^\w\u0600-\u06FF]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def sql_str(val):
    if val is None:
        return "NULL"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (dict, list)):
        return "'" + json.dumps(val, ensure_ascii=False).replace("'", "''") + "'::jsonb"
    s = str(val).replace("'", "''")
    return f"'{s}'"


def generate_seed():
    print("Generating comprehensive seed.sql for all 36 channels...")
    
    enriched_data = {}
    if ENRICHED_FILE.exists():
        enriched_data = json.loads(ENRICHED_FILE.read_text(encoding="utf-8"))
        
    schedule_path = SCHEDULE_FILE if SCHEDULE_FILE.exists() else ROTANA_SCHEDULE_FILE
    schedule_data = json.loads(schedule_path.read_text(encoding="utf-8"))
    programs = schedule_data.get("data", [])
    
    manual_data = {}
    if MANUAL_FILE.exists():
        manual_data = json.loads(MANUAL_FILE.read_text(encoding="utf-8"))

    sql_statements = [
        "-- =============================================================================",
        "-- TV Guide Production Database Seed Data (36 Channels & Full Schedules)",
        "-- Auto-generated: " + datetime.now(timezone.utc).isoformat(),
        "-- =============================================================================",
        "",
        "BEGIN;",
        ""
    ]

    # 1. Channels
    sql_statements.append("-- 1. CHANNELS (36 CHANNELS)")
    channel_id_map = {}
    for ch in ALL_CHANNELS_CATALOG:
        channel_id_map[str(ch["id"])] = ch["id"]
        channel_id_map[ch["source_channel_id"]] = ch["id"]
        stmt = (
            f"INSERT INTO public.channels (id, name, name_ar, name_en, logo_url, source, source_channel_id, country, language, category, display_order) "
            f"VALUES ({ch['id']}, {sql_str(ch['name'])}, {sql_str(ch['name_ar'])}, {sql_str(ch['name_en'])}, {sql_str(ch['logo_url'])}, "
            f"{sql_str(ch['source'])}, {sql_str(ch['source_channel_id'])}, {sql_str(ch['country'])}, {sql_str(ch['language'])}, "
            f"{sql_str(ch['category'])}, {ch['display_order']}) "
            f"ON CONFLICT (source, source_channel_id) DO UPDATE SET "
            f"name = EXCLUDED.name, name_ar = EXCLUDED.name_ar, name_en = EXCLUDED.name_en, logo_url = EXCLUDED.logo_url, display_order = EXCLUDED.display_order;"
        )
        sql_statements.append(stmt)
    sql_statements.append("")

    # 2. Frequencies
    sql_statements.append("-- 2. CHANNEL FREQUENCIES (NILESAT & ARABSAT)")
    freq_id = 1
    for ch in ALL_CHANNELS_CATALOG:
        for f in ch.get("frequencies", []):
            stmt = (
                f"INSERT INTO public.channel_frequencies (id, channel_id, satellite, frequency, polarization, symbol_rate, fec, quality, system, is_encrypted, notes) "
                f"VALUES ({freq_id}, {ch['id']}, {sql_str(f['satellite'])}, {sql_str(f['frequency'])}, {sql_str(f['polarization'])}, "
                f"{sql_str(f['symbol_rate'])}, {sql_str(f.get('fec', '5/6'))}, {sql_str(f.get('quality', 'HD'))}, {sql_str(f.get('system', 'DVB-S2'))}, "
                f"{sql_str(f.get('is_encrypted', False))}, {sql_str(f.get('notes'))}) "
                f"ON CONFLICT (id) DO NOTHING;"
            )
            sql_statements.append(stmt)
            freq_id += 1
    sql_statements.append("")

    # 3. Content
    sql_statements.append("-- 3. CANONICAL CONTENT")
    title_to_content = {}
    for cid_str, meta in enriched_data.items():
        src_title = meta.get("source_title") or meta.get("title_ar")
        if src_title:
            norm = normalize_title(src_title)
            title_to_content[norm] = meta

    next_content_id = max([int(k) for k in enriched_data.keys()] + [0]) + 1
    content_records = {}
    
    for p in programs:
        raw_title = p["title"]
        norm = normalize_title(raw_title)
        if norm not in content_records:
            if norm in title_to_content:
                meta = title_to_content[norm]
                content_records[norm] = {
                    "id": meta.get("content_id") or next_content_id,
                    "content_type": meta.get("content_type", "unknown"),
                    "title_ar": meta.get("title_ar", raw_title),
                    "title_en": meta.get("title_en"),
                    "original_title": meta.get("original_title"),
                    "normalized_title": norm,
                    "release_year": meta.get("release_year"),
                    "tmdb_id": meta.get("tmdb_id"),
                    "tmdb_type": meta.get("tmdb_type"),
                    "poster_path": meta.get("poster_path"),
                    "backdrop_path": meta.get("backdrop_path"),
                    "overview_ar": meta.get("overview_ar"),
                    "overview_en": meta.get("overview_en"),
                    "rating": meta.get("rating"),
                    "genres": meta.get("genres", []),
                    "cast_members": meta.get("cast", []),
                    "runtime_minutes": meta.get("runtime_minutes")
                }
            else:
                content_records[norm] = {
                    "id": next_content_id,
                    "content_type": "movie" if "فيلم" in raw_title else "general",
                    "title_ar": raw_title,
                    "title_en": None,
                    "original_title": None,
                    "normalized_title": norm,
                    "release_year": None,
                    "tmdb_id": None,
                    "tmdb_type": None,
                    "poster_path": None,
                    "backdrop_path": None,
                    "overview_ar": None,
                    "overview_en": None,
                    "rating": None,
                    "genres": [],
                    "cast_members": [],
                    "runtime_minutes": None
                }
                next_content_id += 1

    for norm, c in sorted(content_records.items(), key=lambda x: x[1]["id"]):
        stmt = (
            f"INSERT INTO public.content (id, content_type, title_ar, title_en, original_title, normalized_title, release_year, tmdb_id, tmdb_type, poster_path, backdrop_path, overview_ar, overview_en, rating, genres, cast_members, runtime_minutes) "
            f"VALUES ({c['id']}, {sql_str(c['content_type'])}, {sql_str(c['title_ar'])}, {sql_str(c['title_en'])}, {sql_str(c['original_title'])}, "
            f"{sql_str(c['normalized_title'])}, {sql_str(c['release_year'])}, {sql_str(c['tmdb_id'])}, {sql_str(c['tmdb_type'])}, "
            f"{sql_str(c['poster_path'])}, {sql_str(c['backdrop_path'])}, {sql_str(c['overview_ar'])}, {sql_str(c['overview_en'])}, "
            f"{sql_str(c['rating'])}, {sql_str(c['genres'])}, {sql_str(c['cast_members'])}, {sql_str(c['runtime_minutes'])}) "
            f"ON CONFLICT (id) DO UPDATE SET "
            f"content_type = EXCLUDED.content_type, title_ar = EXCLUDED.title_ar, title_en = EXCLUDED.title_en, original_title = EXCLUDED.original_title, "
            f"release_year = EXCLUDED.release_year, tmdb_id = EXCLUDED.tmdb_id, poster_path = EXCLUDED.poster_path, backdrop_path = EXCLUDED.backdrop_path, "
            f"overview_ar = EXCLUDED.overview_ar, rating = EXCLUDED.rating, genres = EXCLUDED.genres, cast_members = EXCLUDED.cast_members, runtime_minutes = EXCLUDED.runtime_minutes;"
        )
        sql_statements.append(stmt)
    sql_statements.append("")

    # 4. Broadcasts
    sql_statements.append("-- 4. BROADCASTS")
    b_id = 1
    for p in programs:
        raw_ch_id = str(p["channelId"])
        ch_db_id = channel_id_map.get(raw_ch_id, 1)
        norm = normalize_title(p["title"])
        c_id = content_records[norm]["id"]
        
        b_date = p["date"]
        s_time = p["startTime"]
        e_time = p.get("endTime")
        e_date = p.get("endDate") or b_date
        
        start_dt = f"{b_date}T{s_time}:00+03:00"
        end_dt = f"{e_date}T{e_time}:00+03:00" if e_time else None
        source_val = p.get("source", "rotana")
        
        stmt = (
            f"INSERT INTO public.broadcasts (id, channel_id, content_id, source, source_item_id, broadcast_date, start_time, end_time, start_datetime, end_datetime) "
            f"VALUES ({b_id}, {ch_db_id}, {c_id}, {sql_str(source_val)}, {sql_str(str(p['sourceItemId']))}, {sql_str(b_date)}, "
            f"{sql_str(s_time)}, {sql_str(e_time)}, {sql_str(start_dt)}, {sql_str(end_dt)}) "
            f"ON CONFLICT (channel_id, source, source_item_id, start_datetime) DO NOTHING;"
        )
        sql_statements.append(stmt)
        b_id += 1
    sql_statements.append("")

    # Sequences Reset
    sql_statements.append("-- RESET IDENTITY SEQUENCES")
    sql_statements.append("SELECT setval('channels_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.channels));")
    sql_statements.append("SELECT setval('channel_frequencies_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.channel_frequencies));")
    sql_statements.append("SELECT setval('content_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.content));")
    sql_statements.append("SELECT setval('broadcasts_id_seq', (SELECT COALESCE(MAX(id), 1) FROM public.broadcasts));")
    sql_statements.append("")
    sql_statements.append("COMMIT;")
    sql_statements.append("")

    OUTPUT_SQL.write_text("\n".join(sql_statements), encoding="utf-8")
    print(f"Generated {len(sql_statements)} lines of SQL in {OUTPUT_SQL}")
    print(f"Channels: {len(ALL_CHANNELS_CATALOG)}, Content: {len(content_records)}, Broadcasts: {len(programs)}")


if __name__ == "__main__":
    generate_seed()
