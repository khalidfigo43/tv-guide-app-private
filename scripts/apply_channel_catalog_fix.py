import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from collectors.channels_catalog import ALL_CHANNELS_CATALOG
from collectors.logo_provider import get_channel_badge_svg
from scripts.compare_catalog_elcinema import REAL_ELCINEMA
from scripts.verify_full_catalog_mapping import EXACT_1_TO_1_MAP

print(f"Loaded {len(ALL_CHANNELS_CATALOG)} channels from catalog.")

updated_catalog = []
modified_count = 0

for ch in ALL_CHANNELS_CATALOG:
    ch_copy = dict(ch)
    ch_id = ch["id"]
    old_el_id = ch.get("elcinema_id")
    
    # 1. Check if in EXACT_1_TO_1_MAP
    if ch_id in EXACT_1_TO_1_MAP:
        new_el_id = EXACT_1_TO_1_MAP[ch_id]
        if old_el_id != new_el_id:
            print(f"Updating Ch [{ch_id}] {ch.get('name_ar')}: elcinema_id {old_el_id} -> {new_el_id}")
            ch_copy["elcinema_id"] = new_el_id
            modified_count += 1
    else:
        # If channel has an elcinema_id not in REAL_ELCINEMA, nullify it
        if old_el_id and old_el_id not in REAL_ELCINEMA:
            print(f"Removing dead elcinema_id {old_el_id} from Ch [{ch_id}] {ch.get('name_ar')}")
            ch_copy["elcinema_id"] = None
            modified_count += 1

    # 2. Fix Extra News logo
    if ch_id == 38:
        extra_news_badge = get_channel_badge_svg("extra_news", "إكسترا نيوز")
        if ch_copy.get("logo_url") != extra_news_badge:
            print("Updating Extra News logo to official SVG badge")
            ch_copy["logo_url"] = extra_news_badge
            ch_copy["elcinema_id"] = None
            modified_count += 1

    # 3. Fix beIN Movies Action
    if ch_id == 124:
        ch_copy["elcinema_id"] = 1323
        ch_copy["logo_url"] = "https://media0106.elcinema.com/tvguide/1323_2.png"

    updated_catalog.append(ch_copy)

print(f"Total channels modified: {modified_count}")

# Format collectors/channels_catalog.py
file_path = Path("collectors/channels_catalog.py")
new_code = "ALL_CHANNELS_CATALOG = [\n"
for ch in updated_catalog:
    new_code += "    {\n"
    for k, v in ch.items():
        new_code += f"        {repr(k)}: {repr(v)},\n"
    new_code += "    },\n"
new_code += "]\n"

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_code)
print(f"Written updated {file_path}")

# Export channels.json
json_content = json.dumps(updated_catalog, ensure_ascii=False, indent=2)
for p in [Path("data/channels.json"), Path("android/app/src/main/assets/channels.json")]:
    with open(p, "w", encoding="utf-8") as f:
        f.write(json_content)
    print(f"Exported {p}")

print("Done!")

