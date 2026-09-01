import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collectors.channels_catalog import ALL_CHANNELS_CATALOG

ELCINEMA_BASE = "https://elcinema.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9"
}

def parse_elcinema_time(time_text):
    time_text = time_text.strip()
    m = re.search(r"(\d{1,2}):(\d{2})\s*(صباحًا|مساءً|صباحا|مساء)", time_text)
    if not m:
        return None
    hour = int(m.group(1))
    minute = int(m.group(2))
    period = m.group(3)
    if "مساء" in period and hour < 12:
        hour += 12
    elif "صباح" in period and hour == 12:
        hour = 0
    return f"{hour:02d}:{minute:02d}"

def fetch_channel_schedule(elcinema_id, date_str):
    url = f"{ELCINEMA_BASE}/tvguide/{elcinema_id}/"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8")
        
        soup = BeautifulSoup(html, "html.parser")
        items = []
        rows = soup.find_all("div", class_="row")
        
        for row in rows:
            time_el = row.find("span", class_="time") or row.find("li", class_="time")
            if not time_el:
                time_div = row.find("div", class_=re.compile(r"columns|small-3|large-2"))
                if time_div and ("صباح" in time_div.text or "مساء" in time_div.text):
                    time_el = time_div
            if not time_el:
                continue

            time_raw = time_el.text.strip()
            parsed_time = parse_elcinema_time(time_raw)
            if not parsed_time:
                continue

            title_el = row.find("a", href=re.compile(r"/work/\d+/")) or row.find("h3") or row.find("h2")
            if not title_el:
                continue

            title = title_el.text.strip()
            if not title:
                continue

            img_el = row.find("img")
            poster = None
            if img_el:
                poster = img_el.get("src") or img_el.get("data-src") or ""
                if poster.startswith("//"):
                    poster = "https:" + poster
                if "blank" in poster.lower() or not poster.startswith("http"):
                    poster = None

            items.append({
                "time": parsed_time,
                "title": title,
                "poster": poster
            })

        if not items:
            return []

        # Sort by time
        items.sort(key=lambda x: x["time"])
        results = []
        for i in range(len(items)):
            cur = items[i]
            if i + 1 < len(items):
                nxt_time = items[i + 1]["time"]
            else:
                sh, sm = map(int, cur["time"].split(":"))
                eh = (sh + 2) % 24
                nxt_time = f"{eh:02d}:{sm:02d}"

            results.append({
                "title": cur["title"],
                "startTime": cur["time"],
                "endTime": nxt_time,
                "poster": cur.get("poster")
            })

        return results
    except Exception as e:
        return []

def main():
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    tomorrow_str = (today + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Generating fresh schedules for Today ({today_str}) and Tomorrow ({tomorrow_str})...")

    # Load existing schedules to preserve posters, categories, TMDB metadata
    existing_file = Path("android/app/src/main/assets/schedules.json")
    existing_schedules = []
    if existing_file.exists():
        try:
            existing_schedules = json.loads(existing_file.read_text(encoding="utf-8"))
        except Exception:
            existing_schedules = []

    # Map of channel ID -> list of schedules
    existing_by_channel = {}
    title_to_poster = {}
    title_to_overview = {}
    title_to_cast = {}
    title_to_type = {}

    for s in existing_schedules:
        ch_id = s.get("channelId")
        if ch_id:
            existing_by_channel.setdefault(ch_id, []).append(s)
        t = s.get("title")
        if t:
            if s.get("poster") and not s.get("poster", "").startswith("data:"):
                title_to_poster[t] = s.get("poster")
            if s.get("overview"):
                title_to_overview[t] = s.get("overview")
            if s.get("cast"):
                title_to_cast[t] = s.get("cast")
            if s.get("programType"):
                title_to_type[t] = s.get("programType")

    fresh_schedules = []
    live_count = 0

    for ch in ALL_CHANNELS_CATALOG:
        ch_id = ch["id"]
        ch_name = ch["name_ar"]
        ch_logo = ch.get("logo_url")
        is_paid = ch.get("is_paid", False)
        el_id = ch.get("elcinema_id")

        live_items = []
        if el_id:
            live_items = fetch_channel_schedule(el_id, today_str)
            if live_items:
                live_count += 1
                print(f"✓ Fetched {len(live_items)} live items for {ch_name} (ID: {ch_id})")

        if live_items:
            for item in live_items:
                title = item["title"]
                poster = item.get("poster") or title_to_poster.get(title)
                fresh_schedules.append({
                    "channelId": ch_id,
                    "channelName": ch_name,
                    "channelLogo": ch_logo,
                    "title": title,
                    "title_en": None,
                    "date": today_str,
                    "startTime": item["startTime"],
                    "endTime": item["endTime"],
                    "poster": poster or ch_logo,
                    "overview": title_to_overview.get(title, f"عرض تلفزيوني على {ch_name}"),
                    "programType": title_to_type.get(title, "movie" if "سينما" in ch_name or "أفلام" in ch_name else "series" if "دراما" in ch_name or "مسلسلات" in ch_name else "program"),
                    "rating": "7.5",
                    "cast": title_to_cast.get(title, []),
                    "is_paid": is_paid
                })
        else:
            # Smartly roll existing items to today's date
            ch_existing = existing_by_channel.get(ch_id, [])
            if ch_existing:
                for s in ch_existing:
                    item_copy = dict(s)
                    item_copy["date"] = today_str
                    item_copy["channelLogo"] = ch_logo
                    item_copy["is_paid"] = is_paid
                    fresh_schedules.append(item_copy)

    print(f"\nTotal fresh schedule items generated: {len(fresh_schedules)} across {len(ALL_CHANNELS_CATALOG)} channels ({live_count} live scraped)")

    # Save to assets/schedules.json
    existing_file.write_text(json.dumps(fresh_schedules, ensure_ascii=False), encoding="utf-8")
    
    # Save to data/schedules.json for online sync
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    (data_dir / "schedules.json").write_text(json.dumps(fresh_schedules, ensure_ascii=False), encoding="utf-8")
    print("✓ Successfully saved to android/app/src/main/assets/schedules.json and data/schedules.json!")

if __name__ == "__main__":
    main()
