import json

data = json.load(open('data/content_identity_resolution.json', encoding='utf-8'))
for k, v in data.items():
    if v.get('status') == 'REVIEW':
        print(f"=== ID {k}: {v['source_title']} (Channels: {v.get('channels')}) ===")
        for i, c in enumerate(v.get('candidates', [])[:4], 1):
            print(f"  {i}. TMDB: {c.get('tmdb_id')} | Type: {c.get('type')} | Title: {c.get('title')} ({c.get('release_date')}) | Score: {c.get('resolver_score')}")
        print()

