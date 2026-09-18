import re
import sys
import urllib.request
from bs4 import BeautifulSoup
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from collectors.channels_catalog import ALL_CHANNELS_CATALOG
from collectors.elcinema_collector import ELCINEMA_NAME_MAP

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ar,en;q=0.9"
}

def fetch_elcinema_channels():
    req = urllib.request.Request("https://elcinema.com/tvguide/", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8")
    
    soup = BeautifulSoup(html, "html.parser")
    channels = {}
    for a in soup.find_all("a", href=re.compile(r"/tvguide/(\d+)/")):
        m = re.search(r"/tvguide/(\d+)/", a["href"])
        if m:
            cid = int(m.group(1))
            name = a.text.strip() or a.get("title", "").strip()
            if cid not in channels or len(name) > len(channels[cid]):
                channels[cid] = name
    return channels

if __name__ == "__main__":
    elcinema_channels = fetch_elcinema_channels()
    print("=" * 80)
    print(f"ALL {len(elcinema_channels)} CHANNELS ON ELCINEMA TV GUIDE:")
    print("=" * 80)
    for cid, name in sorted(elcinema_channels.items()):
        print(f"{cid}: {name}")

    print("\n" + "=" * 80)
    print("AUDITING ELCINEMA_NAME_MAP:")
    print("=" * 80)
    for k, v in sorted(ELCINEMA_NAME_MAP.items(), key=lambda x: x[1]):
        el_name = elcinema_channels.get(v, "NOT ON HOMEPAGE")
        print(f"'{k}' -> {v} (Actual ElCinema channel: '{el_name}')")

    print("\n" + "=" * 80)
    print("AUDITING ALL_CHANNELS_CATALOG vs ELCINEMA:")
    print("=" * 80)
    for ch in ALL_CHANNELS_CATALOG:
        el_id = ch.get("elcinema_id")
        if el_id:
            el_name = elcinema_channels.get(el_id, "NOT ON HOMEPAGE")
            ch_name = ch.get("name_ar") or ch.get("name_en")
            # Flag if names are suspiciously mismatched
            print(f"Our ch [{ch['id']}] '{ch_name}' -> elcinema_id {el_id} ('{el_name}')")

