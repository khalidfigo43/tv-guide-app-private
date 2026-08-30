import requests
import re

URL = "https://d1rjxhevrfxjk0.cloudfront.net/js/all-files.js?v=5165461"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )
}

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

js = response.text

print("JS SIZE:", len(js))

patterns = [
    r"function\s+getData\s*\(",
    r"getData\s*=\s*function",
    r"getData\s*:\s*function",
    r"getData\s*=\s*\(",
    r"function\s*\([^)]*\)\s*\{[^}]*getData",
]

for pattern in patterns:
    matches = list(re.finditer(pattern, js, re.IGNORECASE))

    print("\n" + "=" * 80)
    print("PATTERN:", pattern)
    print("MATCHES:", len(matches))
    print("=" * 80)

    for match in matches:
        pos = match.start()

        print("\n--- POSITION:", pos, "---")

        start = max(0, pos - 1000)
        end = min(len(js), pos + 5000)

        print(js[start:end])