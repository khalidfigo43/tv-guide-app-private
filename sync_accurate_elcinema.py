import concurrent.futures
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
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
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


def fetch_channel_schedule(cid, today_str):
    url = f"{ELCINEMA_BASE}/tvguide/{cid}/"
    html = ""
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=20) as resp:
                html = resp.read().decode("utf-8")
            if html:
                break
        except Exception:
            time.sleep(0.2)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    boxes = soup.find_all("div", class_=re.compile(r"boxed-category-\d+"))
    items = []

    for box in boxes:
        box_text = re.sub(r"\s+", " ", box.text).strip()
        time_text = ""
        for tag in box.find_all(["li", "span", "p", "div"]):
            m = re.search(r"(\d{1,2}:\d{2}\s*(?:صباحًا|مساءً|صباحا|مساء))", tag.text)
            if m:
                time_text = m.group(1)
                break
        if not time_text:
            m = re.search(r"(\d{1,2}:\d{2}\s*(?:صباحًا|مساءً|صباحا|مساء))", box_text)
            if m:
                time_text = m.group(1)
        if not time_text:
            continue

        parsed_time = parse_elcinema_time(time_text)
        if not parsed_time:
            continue

        # Parse duration
        dur_m = re.search(r"\[(\d+)\s*دقيقة\]", box_text)
        duration_min = int(dur_m.group(1)) if dur_m else None

        title = ""
        no_margin_ul = box.find("ul", class_="no-margin")
        if no_margin_ul:
            for a in no_margin_ul.find_all("a"):
                t = a.text.strip()
                if t and not t.isdigit() and len(t) > 1 and "مفضل" not in t and "ذكرني" not in t and "تقييمك" not in t:
                    title = t
                    break
        if not title:
            for a in box.find_all("a", href=re.compile(r"/work/\d+/")):
                t = a.text.strip()
                if t and not t.isdigit() and len(t) > 1 and "مفضل" not in t and "ذكرني" not in t and "تقييمك" not in t:
                    title = t
                    break

        if not title:
            # Check text before time or first text piece
            parts = box_text.split(time_text)
            before = parts[0].strip()
            before = re.sub(r"\[\d+\s*دقيقة\].*", "", before).strip()
            if before and len(before) > 2 and not before.isdigit():
                title = before
            elif len(parts) > 1:
                after = parts[1].strip()
                after = re.sub(r"\[\d+\s*دقيقة\].*", "", after).strip()
                words = after.split()
                if words and len(words[0]) > 2 and not words[0].isdigit():
                    title = " ".join(words[:4])

        from backend.database_service import clean_canonical_title
        title = clean_canonical_title(title)

        if not title or title.isdigit():
            title = "برنامج تلفزيوني"

        img = box.find("img")
        poster = img.get("data-src") or img.get("src") if img else None
        if poster and poster.startswith("//"):
            poster = "https:" + poster

        items.append({
            "title": title,
            "startTime": parsed_time,
            "raw_time": time_text,
            "duration_min": duration_min,
            "poster": poster
        })

    if not items:
        return []

    for i, it in enumerate(items):
        if it.get("duration_min"):
            sh, sm = map(int, it["startTime"].split(":"))
            tot = sh * 60 + sm + it["duration_min"]
            eh = (tot // 60) % 24
            em = tot % 60
            it["endTime"] = f"{eh:02d}:{em:02d}"
        elif i < len(items) - 1:
            it["endTime"] = items[i + 1]["startTime"]
        else:
            sh, sm = map(int, it["startTime"].split(":"))
            it["endTime"] = f"{(sh + 2) % 24:02d}:{sm:02d}"

    current_date_obj = datetime.strptime(today_str, "%Y-%m-%d")
    last_time_mins = -1
    processed_items = []

    for it in items:
        sh, sm = map(int, it["startTime"].split(":"))
        cur_mins = sh * 60 + sm
        if cur_mins < last_time_mins:
            current_date_obj += timedelta(days=1)
        last_time_mins = cur_mins

        item_date_str = current_date_obj.strftime("%Y-%m-%d")
        eh, em = map(int, it["endTime"].split(":"))
        end_mins = eh * 60 + em
        end_date_obj = current_date_obj + timedelta(days=1) if end_mins < cur_mins else current_date_obj

        processed_items.append({
            "title": it["title"],
            "startTime": it["startTime"],
            "endTime": it["endTime"],
            "date": item_date_str,
            "endDate": end_date_obj.strftime("%Y-%m-%d"),
            "poster": it["poster"],
            "source": "elcinema_live",
            "is_verified": True
        })

    return processed_items


def scrape_channel_task(ch_id, ch_name, el_id, today_str):
    items = fetch_channel_schedule(el_id, today_str)
    return ch_id, ch_name, el_id, items


def run():
    print("=" * 80)
    print("ACCURATE FULL ELCINEMA MULTI-CHANNEL SYNC")
    print("=" * 80)

    today_str = datetime.now().strftime("%Y-%m-%d")
    catalog = [dict(c) for c in ALL_CHANNELS_CATALOG]

    tasks = []
    for ch in catalog:
        el_id = ch.get("elcinema_id")
        if el_id:
            tasks.append((ch["id"], ch["name_ar"], el_id, today_str))

    print(f"Scraping {len(tasks)} verified channels with 6 workers...")
    all_broadcasts = []
    item_id_counter = 900000
    success_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(scrape_channel_task, tid, tname, telid, today_str) for tid, tname, telid, today_str in tasks]
        for f in concurrent.futures.as_completed(futures):
            ch_id, ch_name, el_id, items = f.result()
            if items:
                success_count += 1
                print(f"  ✓ [{ch_id}] {ch_name} (elcinema:{el_id}): {len(items)} broadcasts")
                for it in items:
                    all_broadcasts.append({
                        "channelId": ch_id,
                        "channelName": ch_name,
                        "date": it["date"],
                        "startTime": it["startTime"],
                        "endTime": it["endTime"],
                        "endDate": it["endDate"],
                        "sourceItemId": f"elcinema_{ch_id}_{item_id_counter}",
                        "title": it["title"],
                        "poster": it.get("poster"),
                        "source": "elcinema_live",
                        "is_verified": True
                    })
                    item_id_counter += 1

    print(f"\n✓ Successfully scraped {success_count}/{len(tasks)} channels!")
    print(f"✓ Total Broadcasts: {len(all_broadcasts)}")

    # Update channels_catalog.py
    cat_code = f"# Autogenerated Catalog with Exact ElCinema IDs\nALL_CHANNELS_CATALOG = {json.dumps(catalog, ensure_ascii=False, indent=2)}\n"
    Path("collectors/channels_catalog.py").write_text(cat_code, encoding="utf-8")

    # Save to data/all_channels_schedule.json
    sched_out = {
        "status": "success",
        "channels_count": len(catalog),
        "broadcasts_count": len(all_broadcasts),
        "data": all_broadcasts
    }
    Path("data/all_channels_schedule.json").write_text(json.dumps(sched_out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Saved schedules to data/all_channels_schedule.json")


if __name__ == "__main__":
    run()

