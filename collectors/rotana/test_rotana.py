import requests
from bs4 import BeautifulSoup

URL = "https://rotana.net/ar/streams?channel=439"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
}

print("Connecting to Rotana...")

response = requests.get(
    URL,
    headers=headers,
    timeout=30
)

print("Status:", response.status_code)
print("Final URL:", response.url)
print("HTML size:", len(response.text))

if response.status_code != 200:
    print("Request failed!")
    exit()

soup = BeautifulSoup(response.text, "html.parser")

print("\n=== PAGE TITLE ===")
print(soup.title.get_text(strip=True) if soup.title else "No title")

print("\n=== TEXT SAMPLE ===")

text = soup.get_text("\n", strip=True)

lines = [line.strip() for line in text.splitlines() if line.strip()]

for line in lines[:100]:
    print(line)

print("\n=== DONE ===")