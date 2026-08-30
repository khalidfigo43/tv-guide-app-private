import requests
import re

URL = "https://rotana.net/ar/streams?channel=439"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
}

r = requests.get(URL, headers=headers, timeout=30)
r.raise_for_status()

html = r.text

print("HTML SIZE:", len(html))

patterns = [
    r"function\s+getData",
    r"getData\s*=",
    r"getData\s*\(",
    r"onclick\s*=\s*[\"']getData",
    r"\.ajax\s*\(",
    r"\$\.post\s*\(",
    r"\$\.get\s*\(",
    r"fetch\s*\(",
    r"axios",
]

for pattern in patterns:
    matches = list(re.finditer(pattern, html, re.IGNORECASE))

    print("\n" + "=" * 80)
    print("PATTERN:", pattern)
    print("MATCHES:", len(matches))
    print("=" * 80)

    for m in matches[:10]:
        pos = m.start()

        print("\n--- POSITION:", pos, "---")

        start = max(0, pos - 1500)
        end = min(len(html), pos + 4000)

        print(html[start:end])