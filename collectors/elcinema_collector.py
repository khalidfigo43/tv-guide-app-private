import json
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from collectors.channels_catalog import ALL_CHANNELS_CATALOG

ELCINEMA_BASE = "https://elcinema.com"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9"
}

# Arabic name / keywords matching map to elcinema channel IDs
ELCINEMA_NAME_MAP = {
    "mbc 2": 1128,
    "إم بي سي 2": 1128,
    "mbc 4": 1129,
    "إم بي سي 4": 1129,
    "mbc action": 1211,
    "إم بي سي أكشن": 1211,
    "mbc drama": 1194,
    "إم بي سي دراما": 1194,
    "mbc masr": 1239,
    "إم بي سي مصر": 1239,
    "mbc masr 2": 1278,
    "إم بي سي مصر 2": 1278,
    "mbc iraq": 1340,
    "إم بي سي العراق": 1340,
    "mbc 5": 1354,
    "إم بي سي 5": 1354,
    "mbc bollywood": 1144,
    "إم بي سي بوليود": 1144,
    "روتانا سينما مصر": 1148,
    "روتانا سينما السعودية": 1289,
    "روتانا سينما": 1289,
    "روتانا كوميدي": 1358,
    "روتانا كلاسيك": 1150,
    "روتانا دراما": 1149,
    "روتانا خليجية": 1137,
    "الرسالة": 1143,
    "إل بي سي": 1138,
    "قناة سيما": 1176,
    "سيما": 1176,
    "نايل سينما": 1157,
    "نايل دراما": 1158,
    "نايل كوميدي": 1160,
    "نايل لايف": 1159,
    "ماسبيرو زمان": 1345,
    "الفضائية المصرية": 1119,
    "المصرية": 1119,
    "القناة الأولى المصرية": 1117,
    "القناة الثانية المصرية": 1118,
    "دي إم سي": 1290,
    "dmc": 1290,
    "دي إم سي دراما": 1292,
    "dmc دراما": 1292,
    "أون إي": 1203,
    "on e": 1203,
    "أون دراما": 1134,
    "on drama": 1134,
    "سي بي سي": 1198,
    "cbc": 1198,
    "سي بي سي دراما": 1199,
    "cbc دراما": 1199,
    "سي بي سي سفرة": 1238,
    "cbc سفرة": 1238,
    "الحياة": 1137,
    "قناة الحياة": 1137,
    "الحياة دراما": 1147,
    "النهار": 1193,
    "قناة النهار": 1193,
    "النهار دراما": 1223,
    "النهار سينما": 1200,
    "النهار نور": 1318,
    "المحور": 1145,
    "قناة المحور": 1145,
    "صدى البلد": 1226,
    "صدى البلد 2": 1243,
    "صدى البلد دراما": 1242,
    "القاهرة والناس": 1206,
    "القاهرة والناس 2": 1252,
    "الشمس": 1374,
    "قناة الشمس": 1374,
    "تن": 1297,
    "قناة تن": 1297,
    "ten": 1297,
    "هي": 1395,
    "قناة هي": 1395,
    "الناس": 1162,
    "قناة الناس": 1162,
    "بانوراما فيلم": 1180,
    "بانوراما دراما": 1177,
    "بانوراما دراما 2": 1178,
    "كايرو سينما": 1167,
    "كايرو دراما": 1168,
    "الشاشة أفلام": 1362,
    "الشاشة مسلسلات": 1363,
    "الشاشة كلاسيك": 1364,
    "فاميلي سينما": 1359,
    "فاميلي دراما": 1360,
    "ميلودي أفلام": 1140,
    "توك توك سينما": 1348,
    "اليوم سينما": 1347,
    "ناشيونال جيوغرافيك": 1187,
    "ناشيونال جيوغرافيك وايلد": 1188,
    "الجزيرة الوثائقية": 1135,
    "الوثائقية": 1394,
    "قناة الوثائقية المصرية": 1394,
    "ديسكفري": 1272,
    "ديسكفري بالعربية": 1272,
    "أنيمال بلانيت": 1273,
    "كويست عربية": 1316,
    "تلفزيون دبي": 1169,
    "دبي": 1169,
    "دبي وان": 1173,
    "سما دبي": 1170,
    "دبي زمان": 1315,
    "تلفزيون أبوظبي": 1136,
    "أبو ظبي": 1136,
    "أبوظبي": 1136,
    "الإمارات": 1142,
    "قناة الإمارات": 1142,
    "أبوظبي دراما": 1198,
    "سبيستون": 1154,
    "كرتون نتورك": 1209,
    "كرتون نتورك بالعربية": 1209,
    "ماجد": 1311,
    "قناة ماجد": 1311,
    "وناسة": 1156,
    "قناة وناسة": 1156,
    "زي ألوان": 1261,
    "زي أفلام": 1165,
    "أوسن ياهلا": 1205,
    "osn ياهلا": 1205,
    "أوسن موفيز": 1211,
    "osn movies first": 1391,
    "osn movies action": 1211,
    "ذكريات": 1366,
    "قناة ذكريات": 1366,
    "فنون": 1152,
    "قناة فنون": 1152,
    "الجديد": 1214,
    "قناة الجديد": 1214,
    "mtv اللبنانية": 1215,
    "الأردن": 1314,
    "التلفزيون الأردني": 1314
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


def fetch_all_elcinema_channels():
    print("Scraping all available channels from elcinema.com/tvguide/...")
    try:
        req = urllib.request.Request(f"{ELCINEMA_BASE}/tvguide/", headers=HEADERS)
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode("utf-8")
            
        soup = BeautifulSoup(html, "html.parser")
        discovered = {}

        for a in soup.find_all("a", href=re.compile(r"/tvguide/\d+/")):
            m = re.search(r"/tvguide/(\d+)/", a["href"])
            if not m:
                continue
            cid = int(m.group(1))
            name = a.text.strip()
            img = a.find("img")
            logo = ""
            if img:
                logo = img.get("src") or img.get("data-src") or ""
                if logo and logo.startswith("//"):
                    logo = "https:" + logo

            if cid not in discovered:
                discovered[cid] = {"id": cid, "name": name, "logo": logo}
            elif not discovered[cid]["logo"] and logo:
                discovered[cid]["logo"] = logo
            if not discovered[cid]["name"] and name:
                discovered[cid]["name"] = name
                
        print(f"✓ Found {len(discovered)} channels with official logos on elcinema")
        return discovered
    except Exception as e:
        print(f"Error discovering elcinema channels: {e}")
        return {}


def fetch_channel_schedule(elcinema_id, date_str=None):
    url = f"{ELCINEMA_BASE}/tvguide/{elcinema_id}/"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
            
        soup = BeautifulSoup(html, "html.parser")
        items = []

        for row in soup.find_all("div", class_="boxed-category-1"):
            time_tag = row.find("li")
            title_tag = row.find("ul", class_="no-margin")
            
            if time_tag and title_tag:
                t_link = title_tag.find("a")
                if t_link:
                    raw_time = time_tag.text.strip()
                    title = t_link.text.strip()
                    parsed_time = parse_elcinema_time(raw_time)
                    if parsed_time:
                        # Extract poster if available
                        p_img = row.find("img")
                        poster = p_img.get("data-src") or p_img.get("src") if p_img else None
                        items.append({
                            "title": title,
                            "startTime": parsed_time,
                            "raw_time": raw_time,
                            "poster": poster
                        })
                        
        for i, item in enumerate(items):
            if i < len(items) - 1:
                item["endTime"] = items[i + 1]["startTime"]
            else:
                start_h, start_m = map(int, item["startTime"].split(":"))
                end_h = (start_h + 2) % 24
                item["endTime"] = f"{end_h:02d}:{start_m:02d}"
                
        return items
    except Exception:
        return []


def run_full_elcinema_sync():
    print("=" * 80)
    print("RUNNING ELCINEMA MULTI-CHANNEL LOGO & SCHEDULE SYNC")
    print("=" * 80)
    
    discovered_channels = fetch_all_elcinema_channels()
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Update Channel Logos in catalog
    updated_catalog = []
    catalog_updated_count = 0

    for ch in ALL_CHANNELS_CATALOG:
        ch_copy = dict(ch)
        name_ar = ch["name_ar"]
        name_en = ch["name_en"].lower()
        src_id = str(ch.get("source_channel_id", "")).lower()

        matched_elcinema_id = ch.get("elcinema_id")
        if matched_elcinema_id and matched_elcinema_id in discovered_channels:
            el_info = discovered_channels[matched_elcinema_id]
            if el_info.get("logo") and el_info["logo"].startswith("http"):
                ch_copy["logo_url"] = el_info["logo"]
                ch_copy["elcinema_id"] = matched_elcinema_id
                catalog_updated_count += 1
                
        updated_catalog.append(ch_copy)

    print(f"✓ Updated {catalog_updated_count} channel official logos from elcinema!")

    # Write updated catalog
    cat_code = f"# Autogenerated Catalog with Official ElCinema Logos\nALL_CHANNELS_CATALOG = {json.dumps(updated_catalog, ensure_ascii=False, indent=2)}\n"
    Path("collectors/channels_catalog.py").write_text(cat_code, encoding="utf-8")

    # 2. Fetch live schedules for matched channels
    sched_path = Path("data/all_channels_schedule.json")
    all_broadcasts = []
    if sched_path.exists():
        try:
            data = json.loads(sched_path.read_text(encoding="utf-8"))
            all_broadcasts = data.get("data", [])
        except Exception:
            all_broadcasts = []

    item_id_counter = 700000
    live_channels_count = 0

    # Filter out old elcinema items and old rotana raw items
    all_broadcasts = [b for b in all_broadcasts if b.get("source") != "elcinema_live"]

    for ch in updated_catalog:
        el_id = ch.get("elcinema_id")
        if not el_id:
            continue
            
        live_items = fetch_channel_schedule(el_id, today_str)
        if not live_items:
            continue
            
        live_channels_count += 1
        ch_id = ch["id"]
        src_id = str(ch.get("source_channel_id", ""))
        
        # Remove any existing broadcasts for this channel to prevent duplicate IDs or stale times
        all_broadcasts = [b for b in all_broadcasts if not (b.get("channelId") == ch_id or str(b.get("channelId")) == src_id)]
        
        current_date_obj = datetime.strptime(today_str, "%Y-%m-%d")
        last_time_mins = -1

        for item in live_items:
            start_time = item["startTime"]
            start_h, start_m = map(int, start_time.split(":"))
            cur_time_mins = start_h * 60 + start_m

            # When time resets (e.g. from 23:00 to 01:00), advance date to tomorrow
            if cur_time_mins < last_time_mins:
                current_date_obj += timedelta(days=1)

            last_time_mins = cur_time_mins
            item_date_str = current_date_obj.strftime("%Y-%m-%d")

            end_time = item["endTime"]
            end_h, end_m = map(int, end_time.split(":"))
            end_time_mins = end_h * 60 + end_m
            end_date_obj = current_date_obj + timedelta(days=1) if end_time_mins < cur_time_mins else current_date_obj

            all_broadcasts.append({
                "channelId": ch_id,
                "channelName": ch["name_ar"],
                "date": item_date_str,
                "startTime": start_time,
                "endTime": end_time,
                "endDate": end_date_obj.strftime("%Y-%m-%d"),
                "sourceItemId": f"elcinema_{ch_id}_{item_id_counter}",
                "title": item["title"],
                "poster": item.get("poster"),
                "source": "elcinema_live",
                "is_verified": True
            })
            item_id_counter += 1

    result = {
        "status": "success",
        "channels_count": len(updated_catalog),
        "broadcasts_count": len(all_broadcasts),
        "data": all_broadcasts
    }

    sched_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ Successfully synced {live_channels_count} channels live schedules with {len(all_broadcasts)} broadcasts!")


if __name__ == "__main__":
    run_full_elcinema_sync()
