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

response = requests.get(URL, headers=headers, timeout=30)
response.raise_for_status()

html = response.text

movies = [
    "حاحا وتفاحة",
    "عشان خارجين",
    "عيار ناري",
    "كركر",
    "إبن الحاج أحمد",
    "حملة فرعون",
    "الراقصة والطبال",
    "ابن حميدو",
]

for movie in movies:
    print("\n" + "=" * 80)
    print("MOVIE:", movie)
    print("=" * 80)

    pos = html.find(movie)

    if pos == -1:
        print("NOT FOUND IN RAW HTML")
        continue

    start = max(0, pos - 1200)
    end = min(len(html), pos + len(movie) + 1200)

    print(html[start:end])