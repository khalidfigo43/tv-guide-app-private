import json
import re
import urllib.request
from bs4 import BeautifulSoup
from collectors.channels_catalog import ALL_CHANNELS_CATALOG

url = "https://elcinema.com/tvguide/"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
html = urllib.request.urlopen(req).read().decode("utf-8")
soup = BeautifulSoup(html, "html.parser")

existing_names = set(c["name_ar"].replace("قناة ", "").strip() for c in ALL_CHANNELS_CATALOG)
existing_names.update(c["name_en"].lower().strip() for c in ALL_CHANNELS_CATALOG)

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

print(f"Total elcinema channels: {len(discovered)}")
new_channels = []
for cid, info in discovered.items():
    clean_name = info["name"].replace("قناة ", "").strip()
    is_existing = any(clean_name in ex or ex in clean_name for ex in existing_names)
    if not is_existing and clean_name:
        new_channels.append(info)

print(f"Found {len(new_channels)} NEW channels to add from elcinema:")
for ch in new_channels:
    print(f"  + [{ch['id']}] {ch['name']} -> {ch['logo']}")

