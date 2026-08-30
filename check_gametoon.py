import json
from pathlib import Path

# Load catalog
from collectors.channels_catalog import ALL_CHANNELS_CATALOG

suspicious = []
for c in ALL_CHANNELS_CATALOG:
    txt = (str(c.get("name_ar", "")) + " " + str(c.get("name_en", "")) + " " + str(c.get("name", "")) + " " + str(c.get("category", ""))).lower()
    if any(k in txt for k in ["game", "toon", "sport", "play", "tech", "stream", "e-"]):
        suspicious.append((c.get("id"), c.get("name_ar"), c.get("name_en"), c.get("category")))

print(f"Suspicious / Sport / Game channels ({len(suspicious)}):")
for item in suspicious:
    print(item)

