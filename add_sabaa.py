import json
from pathlib import Path

p = Path("data/enriched_content.json")
data = {}
if p.exists():
    data = json.loads(p.read_text(encoding="utf-8"))

next_id = max(int(k) for k in data.keys()) + 1 if data else 1

sabaa_meta = {
    "content_id": next_id,
    "source_title": "فيلم سبع البرومبة",
    "title_ar": "سبع البرمبة",
    "title_en": "Sabaa El Bromba",
    "content_type": "movie",
    "release_year": 2019,
    "rating": 6.8,
    "poster_path": "/rJ66ooiC5NKto86Nkyr7YCdr4yF.jpg",
    "backdrop_path": "/rJ66ooiC5NKto86Nkyr7YCdr4yF.jpg",
    "overview_ar": "تدور الأحداث في إطار كوميدي رومانسي حول شاب بسيط (عمر) يتنكر في شخصيات متعددة من أبطال السينما للفوز بقلب الفتاة التي يحبها ووالدها.",
    "enriched_at": "2026-08-30T05:20:00"
}

data[str(next_id)] = sabaa_meta
p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Added سبع البرومبة as ID {next_id} in data/enriched_content.json")
