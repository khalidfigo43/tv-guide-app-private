import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from collectors.channels_catalog import ALL_CHANNELS_CATALOG

with open('data/schedules.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

schedules = data if isinstance(data, list) else data.get('schedules', [])
ch_counts = {}
for s in schedules:
    cid = s.get('channel_id')
    ch_counts[cid] = ch_counts.get(cid, 0) + 1

for c in ALL_CHANNELS_CATALOG:
    if 'bein' in str(c.get('source_channel_id', '')).lower() or 'بي إن' in str(c.get('name_ar', '')):
        cid = c['id']
        cnt = ch_counts.get(cid, 0)
        print(f"beIN: ID {cid} ({c.get('name_ar')}) -> {cnt} items, elcinema_id: {c.get('elcinema_id')}")

