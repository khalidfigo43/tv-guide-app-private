import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from collectors.channels_catalog import ALL_CHANNELS_CATALOG

for c in ALL_CHANNELS_CATALOG:
    if c['id'] >= 150:
        print(f"ID: {c['id']}, Name: {c.get('name_ar') or c.get('name_en')}, Source: {c.get('source')}, elcinema_id: {c.get('elcinema_id')}")
