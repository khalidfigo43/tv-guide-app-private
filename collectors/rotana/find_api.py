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

print("=== JAVASCRIPT FILES ===")

scripts = []

for script in soup.find_all("script", src=True):
    src = urljoin(URL, script["src"])

    if src not in scripts:
        scripts.append(src)
        print(src)

print("\n=== SEARCHING JAVASCRIPT ===")

for index, src in enumerate(scripts, 1):

    try:
        js = requests.get(src, headers=headers, timeout=30)

        if js.status_code != 200:
            continue

        text = js.text

        keywords = [
            "getData",
            "ajax",
            "fetch(",
            "$.ajax",
            "$.get",
            "/api/",
        ]

        found = [k for k in keywords if k in text]

        if found:
            print("\n" + "=" * 80)
            print(f"SCRIPT #{index}")
            print(src)
            print("FOUND:", ", ".join(found))
            print("=" * 80)

            # Print context around getData
            pos = text.find("getData")

            if pos != -1:
                start = max(0, pos - 1500)
                end = min(len(text), pos + 3000)

                print(text[start:end])

    except Exception as e:
        print("ERROR:", src, e)

print("\n=== DONE ===")