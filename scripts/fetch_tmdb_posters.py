import concurrent.futures
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# Insert parent dir to import config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import TMDB_ACCESS_TOKEN

HEADERS = {
    "Authorization": f"Bearer {TMDB_ACCESS_TOKEN}",
    "accept": "application/json"
}

CACHE_FILE = Path("data/tmdb_poster_cache.json")

NON_FICTION_PATTERNS = [
    r"^نشرة", r"^موجز", r"^أخبار", r"^اخبار", r"^القرآن", r"^القران",
    r"^صلاة", r"^اذان", r"^أذان", r"^حديث الروح", r"^تلاوة", r"^تلاوه",
    r"^صباح الخير", r"^صباح الورد", r"^بث ليلي", r"^فترة بث",
    r"^الحلقة\s+\d+$", r"^Episode\s+\d+$"
]


def clean_title(s: str) -> str:
    if not s:
        return ""
    s = re.sub(r"^(مسلسل|فيلم|مسرحية|برنامج|كرتون|أنيمي|سلسلة|عرض)\s+", "", s.strip())
    s = re.sub(r"\s+ج\s*\d+", "", s)
    s = re.sub(r"\s+الجزء\s+.*", "", s)
    s = re.sub(r"\s+الموسم\s+.*", "", s)
    s = re.sub(r"\s+s\d+.*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*:\s*الحلقة\s+\d+.*", "", s)
    s = re.sub(r"\s*-\s*الموسم\s+.*", "", s)
    s = re.sub(r"\s*\[.*?\]", "", s)
    s = re.sub(r"\s*\(.*?\)", "", s)
    return s.strip()


def normalize_arabic(text: str) -> str:
    if not text:
        return ""
    s = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    s = re.sub(r"[أإآٱ]", "ا", s)
    s = s.replace("ة", "ه").replace("ى", "ي")
    return re.sub(r"\s+", " ", s).strip()


def query_tmdb(q_text: str) -> dict | None:
    if not q_text or len(q_text) < 2:
        return None
    q = urllib.parse.quote(q_text)
    url = f"https://api.themoviedb.org/3/search/multi?query={q}&language=ar-SA"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            results = data.get("results", [])
            for r in results:
                p = r.get("poster_path")
                if p:
                    media_type = r.get("media_type")
                    # TMDB returns movie, tv, or person. We only want movie or tv
                    if media_type in ("movie", "tv"):
                        overview = r.get("overview")
                        rating = str(round(r.get("vote_average", 7.5), 1)) if r.get("vote_average") else "7.5"
                        return {
                            "poster": f"https://image.tmdb.org/t/p/w500{p}",
                            "overview": overview,
                            "rating": rating,
                            "media_type": media_type
                        }
    except Exception:
        pass
    return None


def search_tmdb(title: str) -> tuple[str, dict | None]:
    for pat in NON_FICTION_PATTERNS:
        if re.search(pat, title.strip()):
            return title, None

    cleaned = clean_title(title)
    if len(cleaned) < 2:
        return title, None

    # Try 1: Exact cleaned title
    res = query_tmdb(cleaned)
    if res:
        return title, res

    # Try 2: Normalized Arabic (e.g. أ -> ا)
    norm = normalize_arabic(cleaned)
    if norm != cleaned:
        res = query_tmdb(norm)
        if res:
            return title, res

    # Try 3: If contains colon, dash, or slash, try the main title part
    if any(sep in cleaned for sep in [":", "-", "/", "–"]):
        for sep in [":", "-", "/", "–"]:
            if sep in cleaned:
                part = cleaned.split(sep)[0].strip()
                if len(part) >= 3:
                    res = query_tmdb(part)
                    if res:
                        return title, res
                    res = query_tmdb(normalize_arabic(part))
                    if res:
                        return title, res

    return title, None


def main():
    print("=" * 80)
    print("COMPREHENSIVE MULTI-THREADED TMDB POSTER ENRICHMENT")
    print("=" * 80)

    # 1. Load existing cache
    cache = {}
    if CACHE_FILE.exists():
        try:
            cache = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except Exception:
            cache = {}
    print(f"Existing cache has {len(cache)} entries")

    # 2. Gather all unique titles from programs, schedules, and git history
    titles_set = set()

    prog_file = Path("data/programs.json")
    if prog_file.exists():
        programs = json.loads(prog_file.read_text(encoding="utf-8"))
        for k, v in programs.items():
            t = v.get("title", k).strip()
            if t:
                titles_set.add(t)

    sched_file = Path("data/schedules.json")
    if sched_file.exists():
        scheds = json.loads(sched_file.read_text(encoding="utf-8"))
        for s in scheds:
            t = s.get("title", "").strip()
            if t:
                titles_set.add(t)

    print(f"Total unique titles in system: {len(titles_set)}")

    # Filter titles: skip if already in cache with a valid poster
    titles_to_fetch = []
    for t in titles_set:
        val = cache.get(t)
        if val and isinstance(val, dict) and val.get("poster"):
            continue
        titles_to_fetch.append(t)

    print(f"Titles needing search: {len(titles_to_fetch)}")

    t0 = time.time()
    found_count = 0
    searched_count = 0

    # Use 16 threads for high throughput without overwhelming TMDB
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        futures = {executor.submit(search_tmdb, t): t for t in titles_to_fetch}
        for future in concurrent.futures.as_completed(futures):
            title, result = future.result()
            searched_count += 1
            if result and result.get("poster"):
                cache[title] = result
                found_count += 1
                if found_count % 50 == 0:
                    print(f"  ✓ [{searched_count}/{len(titles_to_fetch)}] Found: {title} -> {result['poster']}")
            else:
                cache[title] = None

            if searched_count % 500 == 0:
                print(f"... Progress: {searched_count}/{len(titles_to_fetch)} processed, {found_count} new posters found ...")
                # Periodic checkpoint save
                CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")

    elapsed = time.time() - t0
    print("=" * 80)
    print(f"✓ FINISHED in {elapsed:.1f}s. Found {found_count} new posters!")
    print(f"Total valid posters in cache now: {sum(1 for v in cache.values() if v and isinstance(v, dict) and v.get('poster'))}")
    print("=" * 80)

    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Saved updated cache to {CACHE_FILE}")


if __name__ == "__main__":
    main()
