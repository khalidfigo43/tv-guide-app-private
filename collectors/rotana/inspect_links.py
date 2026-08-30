import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

URL = "https://rotana.net/ar/streams?channel=439"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
}

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

soup = BeautifulSoup(response.text, "html.parser")

print("=== LINKS ===")

seen = set()

for a in soup.find_all("a", href=True):
    href = urljoin(URL, a["href"])
    text = a.get_text(" ", strip=True)

    if not text:
        continue

    key = (text, href)

    if key in seen:
        continue

    seen.add(key)

    print(f"\nTEXT: {text}")
    print(f"URL : {href}")

print("\n=== IMAGES ===")

seen_images = set()

for img in soup.find_all("img"):
    src = img.get("src") or img.get("data-src")

    if not src:
        continue

    src = urljoin(URL, src)

    if src in seen_images:
        continue

    seen_images.add(src)

    print(f"\nALT: {img.get('alt')}")
    print(f"SRC: {src}")

print("\n=== DONE ===")