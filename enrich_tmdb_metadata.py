import json
import time
from pathlib import Path
import requests

from config import TMDB_ACCESS_TOKEN

RESOLVED_FILE = Path("data/content_identity_resolution.json")
MANUAL_FILE = Path("data/manual_mappings.json")
OUTPUT_FILE = Path("data/enriched_content.json")

HEADERS = {
    "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
    "accept": "application/json",
}

session = requests.Session()
session.headers.update(HEADERS)


def fetch_tmdb_details(tmdb_id, tmdb_type="movie"):
    endpoint = "movie" if tmdb_type == "movie" else "tv"
    url = f"https://api.themoviedb.org/3/{endpoint}/{tmdb_id}"
    
    # Fetch Arabic details with credits
    params = {
        "language": "ar-SA",
        "append_to_response": "credits,alternative_titles",
    }
    
    try:
        r = session.get(url, params=params, timeout=(5, 15))
        r.raise_for_status()
        data_ar = r.json()
    except Exception as e:
        print(f"  Error fetching AR details for TMDB {tmdb_id}: {e}")
        return None
    
    # Fetch English overview/title fallback if AR overview is empty
    overview_ar = data_ar.get("overview", "")
    overview_en = ""
    title_en = ""
    
    if not overview_ar or not data_ar.get("title") or not data_ar.get("name"):
        try:
            r_en = session.get(url, params={"language": "en-US"}, timeout=(5, 15))
            if r_en.status_code == 200:
                data_en = r_en.json()
                overview_en = data_en.get("overview", "")
                title_en = data_en.get("title") or data_en.get("name") or ""
        except Exception:
            pass
    
    # Extract genres
    genres = [g.get("name") for g in data_ar.get("genres", []) if g.get("name")]
    
    # Extract top cast
    credits = data_ar.get("credits", {})
    cast_list = credits.get("cast", [])
    top_cast = []
    for c in cast_list[:6]:
        top_cast.append({
            "name": c.get("name"),
            "character": c.get("character"),
            "profile_path": c.get("profile_path")
        })
    
    # Date & year
    release_date = data_ar.get("release_date") or data_ar.get("first_air_date") or ""
    release_year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else None
    
    title = data_ar.get("title") or data_ar.get("name") or ""
    original_title = data_ar.get("original_title") or data_ar.get("original_name") or ""
    
    runtime = data_ar.get("runtime")
    if not runtime and data_ar.get("episode_run_time"):
        runtimes = data_ar.get("episode_run_time", [])
        runtime = runtimes[0] if runtimes else None

    return {
        "tmdb_id": tmdb_id,
        "tmdb_type": tmdb_type,
        "title_ar": title,
        "title_en": title_en,
        "original_title": original_title,
        "release_year": release_year,
        "release_date": release_date,
        "poster_path": data_ar.get("poster_path"),
        "backdrop_path": data_ar.get("backdrop_path"),
        "overview_ar": overview_ar or overview_en,
        "overview_en": overview_en,
        "rating": round(float(data_ar.get("vote_average", 0.0)), 1) if data_ar.get("vote_average") is not None else None,
        "vote_count": data_ar.get("vote_count", 0),
        "genres": genres,
        "cast": top_cast,
        "runtime_minutes": runtime
    }


def main():
    if not RESOLVED_FILE.exists():
        print(f"Missing {RESOLVED_FILE}")
        return
        
    resolved_data = json.loads(RESOLVED_FILE.read_text(encoding="utf-8"))
    manual_data = {}
    if MANUAL_FILE.exists():
        manual_data = json.loads(MANUAL_FILE.read_text(encoding="utf-8"))
        
    enriched = {}
    if OUTPUT_FILE.exists():
        try:
            enriched = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
        except Exception:
            enriched = {}

    print("=" * 70)
    print("ENRICHING METADATA FROM TMDB")
    print("=" * 70)

    total = len(resolved_data)
    for idx, (content_id, item) in enumerate(resolved_data.items(), 1):
        source_title = item.get("source_title", "")
        
        # Check manual override first
        target_tmdb_id = None
        target_tmdb_type = "movie"
        content_type = "unknown"
        
        if source_title in manual_data:
            m = manual_data[source_title]
            target_tmdb_id = m.get("tmdb_id")
            target_tmdb_type = m.get("tmdb_type") or "movie"
            content_type = m.get("content_type", "movie")
        elif item.get("status") == "CONFIRMED" and item.get("best_match"):
            bm = item["best_match"]
            target_tmdb_id = bm.get("tmdb_id")
            target_tmdb_type = bm.get("type", "movie")
            content_type = bm.get("type", "movie")
        else:
            # Unresolved or no TMDB
            # Infer content_type from channel type
            ctype = item.get("channel_type")
            if ctype == "movie":
                content_type = "movie"
            elif ctype == "series":
                content_type = "series"
            elif ctype == "program":
                content_type = "program"
            else:
                content_type = "unknown"

        if content_id in enriched and enriched[content_id].get("tmdb_id") == target_tmdb_id:
            continue

        print(f"[{idx}/{total}] {source_title} -> TMDB: {target_tmdb_id} ({target_tmdb_type})")
        
        tmdb_meta = None
        if target_tmdb_id:
            tmdb_meta = fetch_tmdb_details(target_tmdb_id, target_tmdb_type)
            time.sleep(0.15) # respect rate limit

        enriched[content_id] = {
            "content_id": int(content_id),
            "source_title": source_title,
            "content_type": content_type,
            "channels": item.get("channels", []),
            "tmdb_id": target_tmdb_id,
            "tmdb_type": target_tmdb_type if target_tmdb_id else None,
            "title_ar": tmdb_meta.get("title_ar") if tmdb_meta and tmdb_meta.get("title_ar") else source_title,
            "title_en": tmdb_meta.get("title_en") if tmdb_meta else None,
            "original_title": tmdb_meta.get("original_title") if tmdb_meta else None,
            "release_year": tmdb_meta.get("release_year") if tmdb_meta else None,
            "release_date": tmdb_meta.get("release_date") if tmdb_meta else None,
            "poster_path": tmdb_meta.get("poster_path") if tmdb_meta else None,
            "backdrop_path": tmdb_meta.get("backdrop_path") if tmdb_meta else None,
            "overview_ar": tmdb_meta.get("overview_ar") if tmdb_meta else None,
            "overview_en": tmdb_meta.get("overview_en") if tmdb_meta else None,
            "rating": tmdb_meta.get("rating") if tmdb_meta else None,
            "genres": tmdb_meta.get("genres") if tmdb_meta else [],
            "cast": tmdb_meta.get("cast") if tmdb_meta else [],
            "runtime_minutes": tmdb_meta.get("runtime_minutes") if tmdb_meta else None
        }

        # Save progress
        OUTPUT_FILE.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nMetadata enrichment complete! Saved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()

