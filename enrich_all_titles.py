import json
import re
import time
from pathlib import Path
import requests

from config import TMDB_ACCESS_TOKEN

SCHEDULE_FILE = Path("data/all_channels_schedule.json")
ENRICHED_FILE = Path("data/enriched_content.json")

HEADERS = {
    "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
    "accept": "application/json",
}

session = requests.Session()
session.headers.update(HEADERS)


def clean_title_for_search(title):
    t = re.sub(r"^(مسلسل|فيلم|برنامج|مسرحية)\s+", "", title).strip()
    return t


def normalize_ar_letters(text):
    t = text
    for old, new in [("أ", "ا"), ("إ", "ا"), ("آ", "ا"), ("ٱ", "ا"), ("ى", "ي"), ("ة", "ه")]:
        t = t.replace(old, new)
    return t


def search_tmdb(query):
    raw_q = clean_title_for_search(query)
    queries_to_try = [raw_q, normalize_ar_letters(raw_q)]
    
    for q in queries_to_try:
        url = "https://api.themoviedb.org/3/search/multi"
        params = {
            "query": q,
            "language": "ar-SA",
            "include_adult": "false"
        }
        try:
            r = session.get(url, params=params, timeout=(5, 12))
            if r.status_code == 200:
                results = r.json().get("results", [])
                with_posters = [x for x in results if x.get("poster_path") or x.get("backdrop_path")]
                if with_posters:
                    return with_posters[0]
                if results:
                    return results[0]
        except Exception:
            pass
            
    # Try English search fallback
    try:
        r_en = session.get("https://api.themoviedb.org/3/search/multi", params={"query": raw_q, "language": "en-US"}, timeout=(5, 12))
        if r_en.status_code == 200:
            results = r_en.json().get("results", [])
            with_posters = [x for x in results if x.get("poster_path") or x.get("backdrop_path")]
            if with_posters:
                return with_posters[0]
    except Exception:
        pass
        
    return None


def fetch_details(tmdb_id, media_type="movie"):
    endpoint = "movie" if media_type == "movie" else "tv"
    url = f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}"
    params = {
        "language": "ar-SA",
        "append_to_response": "credits",
    }
    try:
        r = session.get(url, params=params, timeout=(5, 12))
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None


def main():
    print("=" * 80)
    print("ENRICHING ALL 36 CHANNEL TITLES FROM TMDB")
    print("=" * 80)

    schedules_data = json.loads(SCHEDULE_FILE.read_text(encoding="utf-8"))
    programs = schedules_data.get("data", [])
    
    enriched = {}
    if ENRICHED_FILE.exists():
        try:
            enriched = json.loads(ENRICHED_FILE.read_text(encoding="utf-8"))
        except Exception:
            enriched = {}

    # Gather all unique titles
    unique_titles = {}
    for p in programs:
        title = p["title"]
        unique_titles[title] = p

    print(f"Total unique program/movie titles across all channels: {len(unique_titles)}")

    next_id = max([int(k) for k in enriched.keys()] + [0]) + 1

    # Map existing enriched by title
    existing_by_title = {}
    for cid_str, meta in enriched.items():
        t = meta.get("source_title") or meta.get("title_ar")
        if t:
            existing_by_title[t] = meta

    for idx, (title, p) in enumerate(unique_titles.items(), 1):
        if title in existing_by_title and existing_by_title[title].get("poster_path"):
            continue

        print(f"[{idx}/{len(unique_titles)}] Searching: {title} ...")
        match = search_tmdb(title)
        
        content_id = next_id
        if title in existing_by_title:
            content_id = existing_by_title[title].get("content_id", next_id)
        else:
            next_id += 1

        if match:
            media_type = match.get("media_type", "movie")
            tmdb_id = match.get("id")
            details = fetch_details(tmdb_id, media_type)
            
            poster = match.get("poster_path")
            backdrop = match.get("backdrop_path")
            overview = (details.get("overview") if details else "") or match.get("overview") or ""
            rating = match.get("vote_average") or (details.get("vote_average") if details else None)
            
            # Cast
            cast_list = []
            if details and details.get("credits"):
                for c in details["credits"].get("cast", [])[:5]:
                    cast_list.append({
                        "name": c.get("name"),
                        "character": c.get("character"),
                        "profile_path": c.get("profile_path")
                    })
                    
            # Genres
            genres = []
            if details and details.get("genres"):
                genres = [g.get("name") for g in details["genres"] if g.get("name")]

            # Year
            date_str = match.get("release_date") or match.get("first_air_date") or ""
            year = int(date_str[:4]) if len(date_str) >= 4 and date_str[:4].isdigit() else None
            
            title_ar = match.get("title") or match.get("name") or title
            title_en = match.get("original_title") or match.get("original_name")

            enriched[str(content_id)] = {
                "content_id": content_id,
                "source_title": title,
                "content_type": "movie" if media_type == "movie" else "series",
                "tmdb_id": tmdb_id,
                "tmdb_type": media_type,
                "title_ar": title_ar,
                "title_en": title_en,
                "original_title": match.get("original_title") or match.get("original_name"),
                "release_year": year,
                "release_date": date_str,
                "poster_path": poster,
                "backdrop_path": backdrop,
                "overview_ar": overview,
                "overview_en": overview,
                "rating": round(float(rating), 1) if rating else None,
                "genres": genres,
                "cast": cast_list,
                "runtime_minutes": details.get("runtime") if details else None
            }
            print(f"  ✓ Found TMDB {tmdb_id}: {title_ar} ({year}) - Poster: {poster}")
        else:
            enriched[str(content_id)] = {
                "content_id": content_id,
                "source_title": title,
                "content_type": "program",
                "tmdb_id": None,
                "tmdb_type": None,
                "title_ar": title,
                "title_en": None,
                "original_title": None,
                "release_year": None,
                "poster_path": None,
                "backdrop_path": None,
                "overview_ar": f"برنامج تلفزيوني يُعرض على القنوات الفضائية.",
                "rating": None,
                "genres": [],
                "cast": [],
                "runtime_minutes": None
            }
            print(f"  - No TMDB match for: {title}")

        # Save progress
        ENRICHED_FILE.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(0.12)

    print("\nEnrichment complete! Saved to:", ENRICHED_FILE)


if __name__ == "__main__":
    main()

