import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from collectors.channels_catalog import ALL_CHANNELS_CATALOG

ENRICHED_PATH = Path("data/enriched_content.json")
SCHEDULE_PATH = Path("data/all_channels_schedule.json")
ROTANA_SCHEDULE_PATH = Path("data/rotana_schedule.json")

# Default timezone for the application (Riyadh / AST +03:00)
TIMEZONE_OFFSET = timedelta(hours=3)


def clean_canonical_title(text: str) -> str:
    if not text:
        return ""
    t = str(text).strip()
    # Strip any time patterns like 06:00 صباحًا, 12:00 مساءً, 7.00 صباحا, [120 دقيقة], etc.
    t = re.sub(r"\d{1,2}[:.]\d{2}\s*(?:صباحًا|مساءً|صباحا|مساء|ص|م)?", "", t)
    t = re.sub(r"\[\d+\s*دقيقة\].*", "", t)
    t = re.sub(r"\b(?:صباحًا|مساءً|صباحا|مساء)\b", "", t)
    # Strip leading prefixes: مسلسل, فيلم, برنامج, سهرة, مسرحية
    t = re.sub(r"^(?:مسلسل|فيلم|برنامج|سهرة|مسرحية)\s+", "", t, flags=re.IGNORECASE)
    # Strip trailing (إعادة), [إعادة], - إعادة, (مباشر), etc.
    t = re.sub(r"[\(\[\{]\s*(?:إعادة|اعادة|مباشر|بث مباشر|مترجم|مدبلج|حصري|حصرية|خاصة)\s*[\)\]\}]", "", t, flags=re.IGNORECASE)
    t = re.sub(r"[-–—:]\s*(?:إعادة|اعادة|مباشر|بث مباشر)\s*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+(?:إعادة|اعادة)\s*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+", " ", t).strip()
    return t if len(t) > 1 and not t.isdigit() else "برنامج تلفزيوني"


def normalize_arabic(text: str) -> str:
    if not text:
        return ""
    text = clean_canonical_title(str(text))
    text = text.lower().strip()
    text = re.sub(r"[\u064B-\u065F\u0670]", "", text)
    replacements = {"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ة": "ه"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    arabic_digits = {"٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4", "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9"}
    for old, new in arabic_digits.items():
        text = text.replace(old, new)
    text = text.replace("ـ", "")
    text = re.sub(r"[^\w\u0600-\u06FF]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


class TVGuideService:
    def __init__(self):
        self.channels = ALL_CHANNELS_CATALOG
        self._last_loaded = 0
        self.reload()

    def reload(self):
        self.enriched_meta = {}
        self._title_lookup = {}
        if ENRICHED_PATH.exists():
            try:
                raw_meta = json.loads(ENRICHED_PATH.read_text(encoding="utf-8"))
                for k, meta in raw_meta.items():
                    s_title = clean_canonical_title(meta.get("source_title") or "")
                    ar_title = clean_canonical_title(meta.get("title_ar") or "")
                    meta["title_ar"] = ar_title or meta.get("title_ar")
                    self.enriched_meta[k] = meta
                    if s_title:
                        self._title_lookup[normalize_arabic(s_title)] = meta
                    if ar_title:
                        self._title_lookup[normalize_arabic(ar_title)] = meta
            except Exception:
                self.enriched_meta = {}
                self._title_lookup = {}
                
        # Load all broadcast schedules
        self.schedules = []
        path_to_use = SCHEDULE_PATH if SCHEDULE_PATH.exists() else ROTANA_SCHEDULE_PATH
        if path_to_use.exists():
            try:
                data = json.loads(path_to_use.read_text(encoding="utf-8"))
                raw_list = data.get("data", []) if isinstance(data, dict) else data
                for p in raw_list:
                    p["title"] = clean_canonical_title(p.get("title", ""))
                    self.schedules.append(p)
                self._last_loaded = path_to_use.stat().st_mtime
            except Exception:
                self.schedules = []

    def _ensure_fresh(self):
        path_to_use = SCHEDULE_PATH if SCHEDULE_PATH.exists() else ROTANA_SCHEDULE_PATH
        if path_to_use.exists() and path_to_use.stat().st_mtime > self._last_loaded:
            self.reload()

    def _get_enriched_by_title(self, title: str) -> Dict[str, Any]:
        norm = normalize_arabic(title)
        return self._title_lookup.get(norm, {})

    def get_channels(self) -> List[Dict[str, Any]]:
        return self.channels

    def get_channel_by_id(self, channel_id: int) -> Optional[Dict[str, Any]]:
        for ch in self.channels:
            if ch["id"] == channel_id:
                return ch
        return None

    def get_channel_schedule(self, channel_id: int, date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        self._ensure_fresh()
        ch = self.get_channel_by_id(channel_id)
        if not ch:
            return []
            
        results = []
        for p in self.schedules:
            p_ch_id = p.get("channelId")
            if p_ch_id == channel_id or str(p_ch_id) == ch.get("source_channel_id"):
                p_date = p.get("date")
                if date_str and p_date != date_str:
                    continue
                    
                meta = self._get_enriched_by_title(p["title"])
                results.append({
                    "broadcast_id": p.get("sourceItemId"),
                    "channel_id": channel_id,
                    "channel_name": ch["name_ar"],
                    "channel_logo": ch["logo_url"],
                    "title": p["title"],
                    "content_type": meta.get("content_type", "movie" if "سينما" in ch["name_ar"] or "aflam" in ch["name_en"].lower() else "general"),
                    "release_year": meta.get("release_year"),
                    "rating": meta.get("rating"),
                    "poster_path": p.get("poster") or meta.get("poster_path"),
                    "backdrop_path": p.get("backdrop") or meta.get("backdrop_path") or p.get("poster"),
                    "overview": p.get("overview") or meta.get("overview_ar") or meta.get("overview_en"),
                    "date": p_date,
                    "start_time": p.get("startTime"),
                    "end_time": p.get("endTime"),
                    "start_datetime": f"{p_date}T{p.get('startTime')}:00+03:00",
                    "end_datetime": f"{p.get('endDate') or p_date}T{p.get('endTime')}:00+03:00" if p.get("endTime") else None,
                })
        return results

    def get_now_airing(self, reference_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        self._ensure_fresh()
        now_list = []
        now_dt = reference_time or datetime.now()
        today_str = now_dt.strftime("%Y-%m-%d")
        ref_hour_str = now_dt.strftime("%H:%M")
        
        for ch in self.channels:
            ch_id = ch["id"]
            src_id = ch.get("source_channel_id")
            
            # Prefer today's broadcast schedule
            ch_progs = [p for p in self.schedules if (p.get("channelId") == ch_id or str(p.get("channelId")) == src_id) and p.get("date") == today_str]
            if not ch_progs:
                ch_progs = [p for p in self.schedules if p.get("channelId") == ch_id or str(p.get("channelId")) == src_id]
            if not ch_progs:
                continue
                
            # Find active program
            active = None
            for p in ch_progs:
                s_time = p.get("startTime", "00:00")
                e_time = p.get("endTime", "23:59")
                if s_time <= ref_hour_str < e_time or (s_time > e_time and (ref_hour_str >= s_time or ref_hour_str < e_time)):
                    active = p
                    break
            
            if not active:
                active = ch_progs[0]

            # Calculate dynamic remaining minutes & progress percentage
            p_date = active.get("date") or today_str
            e_date = active.get("endDate") or p_date
            s_time = active.get("startTime", "00:00")
            e_time = active.get("endTime", "23:59")

            try:
                s_dt = datetime.strptime(f"{p_date} {s_time}", "%Y-%m-%d %H:%M")
                e_dt = datetime.strptime(f"{e_date} {e_time}", "%Y-%m-%d %H:%M")
                if e_dt <= s_dt:
                    e_dt += timedelta(days=1)
                total_sec = max(60.0, (e_dt - s_dt).total_seconds())
                elapsed_sec = max(0.0, (now_dt - s_dt).total_seconds())
                remaining_sec = max(0.0, (e_dt - now_dt).total_seconds())
                remaining_min = int(round(remaining_sec / 60.0))
                progress_pct = min(100, max(0, int(round((elapsed_sec / total_sec) * 100.0))))
            except Exception:
                remaining_min = 30
                progress_pct = 50

            meta = self._get_enriched_by_title(active["title"])
            now_list.append({
                "broadcast_id": active.get("sourceItemId"),
                "channel_id": ch["id"],
                "channel_name": ch["name_ar"],
                "channel_logo": ch["logo_url"],
                "content_id": meta.get("content_id", 1),
                "title": active["title"],
                "title_en": meta.get("title_en"),
                "content_type": meta.get("content_type", "movie" if "سينما" in ch["name_ar"] else "general"),
                "release_year": meta.get("release_year"),
                "rating": meta.get("rating"),
                "poster_path": active.get("poster") or meta.get("poster_path"),
                "backdrop_path": active.get("backdrop") or meta.get("backdrop_path") or active.get("poster"),
                "overview": active.get("overview") or meta.get("overview_ar") or meta.get("overview_en"),
                "start_time": s_time,
                "end_time": e_time,
                "start_datetime": f"{p_date}T{s_time}:00+03:00",
                "end_datetime": f"{e_date}T{e_time}:00+03:00",
                "remaining_minutes": remaining_min,
                "progress_percent": progress_pct
            })
        return now_list

    def get_next_airing(self, reference_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        self._ensure_fresh()
        next_list = []
        now_dt = reference_time or datetime.now()
        today_str = now_dt.strftime("%Y-%m-%d")
        ref_hour_str = now_dt.strftime("%H:%M")

        for ch in self.channels:
            ch_id = ch["id"]
            src_id = ch.get("source_channel_id")
            ch_progs = [p for p in self.schedules if (p.get("channelId") == ch_id or str(p.get("channelId")) == src_id) and p.get("date") == today_str]
            if not ch_progs:
                ch_progs = [p for p in self.schedules if p.get("channelId") == ch_id or str(p.get("channelId")) == src_id]
            if not ch_progs:
                continue

            # Find active index
            active_idx = 0
            for i, p in enumerate(ch_progs):
                s_time = p.get("startTime", "00:00")
                e_time = p.get("endTime", "23:59")
                if s_time <= ref_hour_str < e_time or (s_time > e_time and (ref_hour_str >= s_time or ref_hour_str < e_time)):
                    active_idx = i
                    break

            next_idx = (active_idx + 1) % len(ch_progs)
            p = ch_progs[next_idx]
            p_date = p.get("date") or today_str
            e_date = p.get("endDate") or p_date

            meta = self._get_enriched_by_title(p["title"])
            next_list.append({
                "broadcast_id": p.get("sourceItemId"),
                "channel_id": ch["id"],
                "channel_name": ch["name_ar"],
                "channel_logo": ch["logo_url"],
                "content_id": meta.get("content_id", 1),
                "title": p["title"],
                "title_en": meta.get("title_en"),
                "content_type": meta.get("content_type", "movie"),
                "release_year": meta.get("release_year"),
                "rating": meta.get("rating"),
                "poster_path": p.get("poster") or meta.get("poster_path"),
                "backdrop_path": p.get("backdrop") or meta.get("backdrop_path") or p.get("poster"),
                "overview": p.get("overview") or meta.get("overview_ar") or meta.get("overview_en"),
                "start_time": p.get("startTime"),
                "end_time": p.get("endTime"),
                "start_datetime": f"{p_date}T{p.get('startTime')}:00+03:00",
                "end_datetime": f"{e_date}T{p.get('endTime')}:00+03:00" if p.get("endTime") else None,
            })
        return next_list

    def get_movies(self, page: int = 1, limit: int = 36, genre: Optional[str] = None, content_type: Optional[str] = None) -> Dict[str, Any]:
        self._ensure_fresh()
        library_items = []
        seen_titles = {}
        
        # Map channel names for quick lookup
        ch_map = {c["id"]: c["name_ar"] for c in self.channels}
        
        # Index all distinct live titles with stable deterministic IDs
        self._title_by_id = {}
        self._id_by_title = {}
        
        title_id_counter = 1
        for p in self.schedules:
            title = p.get("title", "").strip()
            if not title or len(title) < 2:
                continue
                
            norm = normalize_arabic(title)
            ch_id = p.get("channelId")
            ch_name = ch_map.get(ch_id, p.get("channelName", "قناة فضائية"))
            
            if norm in seen_titles:
                # Add channel/broadcast reference
                seen_titles[norm]["channels"].add(ch_name)
                seen_titles[norm]["broadcasts_count"] += 1
                if not seen_titles[norm]["poster_path"] and p.get("poster"):
                    seen_titles[norm]["poster_path"] = p.get("poster")
                continue
                
            meta = self._get_enriched_by_title(title)
            meta_type = meta.get("content_type", "")
            assigned_id = meta.get("content_id") or (10000 + title_id_counter)
            title_id_counter += 1
            
            self._title_by_id[assigned_id] = title
            self._id_by_title[norm] = assigned_id

            # Smart granular category deduction
            title_l = title.lower()
            ch_l = ch_name.lower()
            genres = meta.get("genres", [])
            is_anim_or_kids = (
                "Animation" in genres or "Kids" in genres or "Family" in genres or
                any(w in title_l for w in [
                    "lego", "barbie", "croods", "pingu", "duplo", "bing", "princess", "مشمش", "كارتون", "كرتون",
                    "انمي", "أنمي", "anime", "animation", "cartoon", "kids", "توم وجيري", "شريك", "سبيستون",
                    "spacetoon", "ماجد", "ميكي", "سنفور", "سمبا", "كونان", "دراغون", "توم و جيري", "shrek",
                    "sponge", "sonic", "pokemon", "naruto", "disney", "pixar", "peppa", "paw patrol", "cocomelon",
                    "dora", "gumball", "غامبول", "سبونج", "سندباد", "ماروكو", "عدنان ولينا", "كابتن ماجد", "ben 10",
                    "بن 10", "powerpuff", "charlie and lola", "tee and mo", "shark tale", "happy feet", "prince of egypt",
                    "منصور", "dragon", "dragons", "تنانين", "مغامرات", "افتتح يا سمسم", "افتح يا سمسم", "ابطال",
                    "ون بيس", "one piece", "ناروتو", "الدببة الثلاثة", "يحيا انجلو", "انجلو", "فتيات القوة"
                ]) or any(k in ch_l for k in ["سبيستون", "spacetoon", "ماجد", "نتورك", "أطفال", "kids", "ديزني"])
            )
            
            is_doc = (
                "Documentary" in genres or
                any(w in title_l for w in ["وثائقي", "وثائقية", "استكشاف", "عالم الحيوان", "planet", "wild", "geography", "history", "space", "cosmos", "ocean"]) or
                any(k in ch_l for k in ["geographic", "discovery", "ناشيونال", "وثائقية", "وثائقي"])
            )

            is_sports = (
                any(w in title_l for w in ["مباراة", "دوري", "كأس", "بطولة", "ملخص", "رياضة", "sports", "stadium", "match", "championship"]) or
                any(k in ch_l for k in ["sport", "رياضة", "أون تايم", "الكاس"])
            )

            is_series = (
                meta_type in ["tv", "series"] or
                any(w in title_l for w in ["مسلسل", "حكايات", "ج1", "ج2", "ج3", "ج4", "ج5", "الموسم", "season", "s1", "s2", "s3", "s4", "s5"]) or
                any(k in ch_l for k in ["دراما", "drama", "مسلسلات"])
            )

            if is_anim_or_kids:
                c_type = "kids"
            elif is_doc:
                c_type = "documentary"
            elif is_sports:
                c_type = "sports"
            elif is_series and not any(w in title_l for w in ["فيلم", "film", "movie"]):
                c_type = "series"
            else:
                is_foreign = (
                    any(w in ch_l for w in ["mbc 2", "mbc max", "mbc action", "star movies", "osn", "bein", "hollywood", "action"]) or
                    bool(re.search(r"^[a-zA-Z0-9\s:,'\.\-\&]+$", title))
                )
                c_type = "foreign_movies" if is_foreign else "arabic_movies"

            item_data = {
                "id": assigned_id,
                "title_ar": meta.get("title_ar", title),
                "title_en": meta.get("title_en"),
                "original_title": meta.get("original_title"),
                "content_type": c_type,
                "release_year": meta.get("release_year"),
                "rating": meta.get("rating"),
                "poster_path": p.get("poster") or meta.get("poster_path"),
                "backdrop_path": meta.get("backdrop_path") or p.get("poster"),
                "overview": meta.get("overview_ar") or meta.get("overview_en"),
                "genres": genres,
                "cast": meta.get("cast", []),
                "runtime_minutes": meta.get("runtime_minutes"),
                "channels": {ch_name},
                "broadcasts_count": 1
            }
            seen_titles[norm] = item_data

        # Filter by content_type / genre
        for norm, item in seen_titles.items():
            item["channels"] = list(item["channels"])
            
            if content_type and content_type != "all":
                if content_type == "movies" and item["content_type"] not in ["movie", "arabic_movies", "foreign_movies"]:
                    continue
                elif content_type == "arabic_movies" and item["content_type"] != "arabic_movies":
                    continue
                elif content_type == "foreign_movies" and item["content_type"] != "foreign_movies":
                    continue
                elif content_type == "series" and item["content_type"] != "series":
                    continue
                elif content_type in ["kids", "anime", "animation", "cartoon"] and item["content_type"] != "kids":
                    continue
                elif content_type == "documentary" and item["content_type"] != "documentary":
                    continue
                elif content_type == "sports" and item["content_type"] != "sports":
                    continue
                    
            if genre and genre not in item.get("genres", []):
                continue
                
            library_items.append(item)

        # Sort by: has poster first, then number of airings, then rating
        library_items.sort(
            key=lambda x: (
                x["poster_path"] is not None and len(str(x["poster_path"])) > 5,
                x["broadcasts_count"],
                x["rating"] or 0
            ),
            reverse=True
        )
        
        total = len(library_items)
        start = (page - 1) * limit
        end = start + limit
        paged = library_items[start:end]
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "results": paged
        }

    def get_content_details(self, content_id: int) -> Optional[Dict[str, Any]]:
        self._ensure_fresh()
        meta = None
        target_title = None
        
        # 1. Check if content_id maps to an enriched TMDB item
        meta = self.enriched_meta.get(str(content_id))
        if not meta:
            for m in self.enriched_meta.values():
                if m.get("content_id") == content_id:
                    meta = m
                    break

        if meta:
            target_title = meta.get("source_title") or meta.get("title_ar")
        elif hasattr(self, "_title_by_id") and content_id in self._title_by_id:
            target_title = self._title_by_id[content_id]
            meta = self._get_enriched_by_title(target_title)
        else:
            # Reconstruct title index from schedules
            title_id_counter = 1
            for p in self.schedules:
                t = p.get("title", "").strip()
                if not t: continue
                assigned_id = (self._get_enriched_by_title(t).get("content_id")) or (10000 + title_id_counter)
                title_id_counter += 1
                if assigned_id == content_id:
                    target_title = t
                    meta = self._get_enriched_by_title(t)
                    break

        if not target_title and not meta:
            return None

        norm_target = normalize_arabic(target_title)
        
        # Group all broadcasts across ALL channels for this exact title
        airings = []
        sample_poster = None
        for p in self.schedules:
            if normalize_arabic(p.get("title", "")) == norm_target:
                if not sample_poster and p.get("poster"):
                    sample_poster = p.get("poster")
                ch = self.get_channel_by_id(p["channelId"])
                airings.append({
                    "broadcast_id": p.get("sourceItemId"),
                    "channel_id": p["channelId"],
                    "channel_name": ch["name_ar"] if ch else p.get("channelName"),
                    "channel_logo": ch["logo_url"] if ch else None,
                    "date": p.get("date"),
                    "start_time": p.get("startTime"),
                    "end_time": p.get("endTime"),
                    "start_datetime": f"{p.get('date')}T{p.get('startTime')}:00+03:00",
                    "end_datetime": f"{p.get('endDate') or p.get('date')}T{p.get('endTime')}:00+03:00" if p.get("endTime") else None,
                })

        meta = meta or {}
        return {
            "id": content_id,
            "title_ar": meta.get("title_ar", target_title),
            "title_en": meta.get("title_en"),
            "original_title": meta.get("original_title"),
            "content_type": meta.get("content_type", "movie"),
            "release_year": meta.get("release_year"),
            "rating": meta.get("rating"),
            "poster_path": meta.get("poster_path") or sample_poster,
            "backdrop_path": meta.get("backdrop_path") or sample_poster,
            "overview": meta.get("overview_ar") or meta.get("overview_en") or f"يعرض على القنوات الفضائية بمواعيد البث الموضحة أدناه.",
            "genres": meta.get("genres", []),
            "cast": meta.get("cast", []),
            "runtime_minutes": meta.get("runtime_minutes"),
            "tmdb_id": meta.get("tmdb_id"),
            "airings_count": len(airings),
            "airings": airings
        }

    def search(self, query: str, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        if not query:
            return []
            
        norm_q = normalize_arabic(query)
        q_lower = query.lower().strip()
        
        # 1. Search across distinct live library titles (from actual broadcast schedules)
        library = self.get_movies(limit=5000, content_type=content_type).get("results", [])
        
        matches = []
        seen_norm_titles = set()
        
        for item in library:
            title_ar = item.get("title_ar") or ""
            norm_title = normalize_arabic(title_ar)
            if norm_title in seen_norm_titles:
                continue
                
            title_en = (item.get("title_en") or "").lower()
            orig_title = (item.get("original_title") or "").lower()
            
            score = 0
            if norm_q == norm_title:
                score = 100
            elif norm_q in norm_title or norm_title in norm_q:
                score = 85
            elif q_lower in title_en or q_lower in orig_title:
                score = 75
            else:
                q_tokens = norm_q.split()
                matched = sum(1 for t in q_tokens if t in norm_title)
                if matched > 0:
                    score = int((matched / len(q_tokens)) * 65)
                    
            if score > 0:
                seen_norm_titles.add(norm_title)
                matches.append({
                    "id": item["id"],
                    "title_ar": title_ar,
                    "title_en": item.get("title_en"),
                    "content_type": item.get("content_type"),
                    "release_year": item.get("release_year"),
                    "rating": item.get("rating"),
                    "poster_path": item.get("poster_path"),
                    "backdrop_path": item.get("backdrop_path"),
                    "overview": item.get("overview"),
                    "score": score
                })
                
        # 2. Also search enriched_meta for catalog titles
        for meta in self.enriched_meta.values():
            ctype = meta.get("content_type", "movie")
            if content_type and ctype != content_type:
                continue
                
            title_ar = clean_canonical_title(meta.get("title_ar") or meta.get("source_title") or "")
            norm_title = normalize_arabic(title_ar)
            if norm_title in seen_norm_titles:
                continue
                
            title_en = (meta.get("title_en") or "").lower()
            orig_title = (meta.get("original_title") or "").lower()
            
            score = 0
            if norm_q == norm_title:
                score = 90
            elif norm_q in norm_title:
                score = 70
            elif q_lower in title_en or q_lower in orig_title:
                score = 65
            else:
                q_tokens = norm_q.split()
                matched = sum(1 for t in q_tokens if t in norm_title)
                if matched > 0:
                    score = int((matched / len(q_tokens)) * 50)
                    
            if score > 0:
                seen_norm_titles.add(norm_title)
                matches.append({
                    "id": meta.get("content_id"),
                    "title_ar": title_ar,
                    "title_en": meta.get("title_en"),
                    "content_type": ctype,
                    "release_year": meta.get("release_year"),
                    "rating": meta.get("rating"),
                    "poster_path": meta.get("poster_path"),
                    "backdrop_path": meta.get("backdrop_path"),
                    "overview": meta.get("overview_ar") or meta.get("overview_en"),
                    "score": score
                })
                
        matches.sort(key=lambda x: (x["score"], x["poster_path"] is not None, x["rating"] or 0), reverse=True)
        return matches[:30]

    # Reminders Management
    def add_reminder(self, reminder_data: Dict[str, Any]) -> Dict[str, Any]:
        reminders_file = Path("data/user_reminders.json")
        reminders = []
        if reminders_file.exists():
            try:
                reminders = json.loads(reminders_file.read_text(encoding="utf-8"))
            except Exception:
                reminders = []
                
        # Generate ID if missing
        r_id = reminder_data.get("id") or f"rem_{int(datetime.now().timestamp()*1000)}"
        reminder_data["id"] = r_id
        reminder_data["created_at"] = datetime.now().isoformat()
        
        # Remove existing for same broadcast/user if any
        reminders = [r for r in reminders if r.get("id") != r_id and not (r.get("broadcast_id") == reminder_data.get("broadcast_id") and r.get("user_id") == reminder_data.get("user_id"))]
        reminders.append(reminder_data)
        
        reminders_file.write_text(json.dumps(reminders, ensure_ascii=False, indent=2), encoding="utf-8")
        return reminder_data

    def get_reminders(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        reminders_file = Path("data/user_reminders.json")
        if not reminders_file.exists():
            return []
        try:
            reminders = json.loads(reminders_file.read_text(encoding="utf-8"))
            if user_id:
                return [r for r in reminders if r.get("user_id") == user_id]
            return reminders
        except Exception:
            return []

    def delete_reminder(self, reminder_id: str) -> bool:
        reminders_file = Path("data/user_reminders.json")
        if not reminders_file.exists():
            return False
        try:
            reminders = json.loads(reminders_file.read_text(encoding="utf-8"))
            filtered = [r for r in reminders if r.get("id") != reminder_id]
            reminders_file.write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")
            return len(filtered) < len(reminders)
        except Exception:
            return False


tv_service = TVGuideService()
