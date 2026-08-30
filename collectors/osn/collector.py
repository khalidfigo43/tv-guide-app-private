import concurrent.futures
import json
import os
import re
import ssl
import sys
import time
import urllib.request
from base64 import b64decode, b64encode
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# Official AES Key & IV for OSN client API
KEY = bytes.fromhex("65a04b9b5591f27c837fac433274b494403e0eec5b43698060c28e1162d4460f")
IV = bytes.fromhex("b7cc0a48d6d023bc1a2a670953ec5622")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://www.osn.com/ar-eg/watch/tv-schedule",
}


def encrypt_client(plaintext: str) -> str:
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV))
    encryptor = cipher.encryptor()
    ct = encryptor.update(padded_data) + encryptor.finalize()
    return b64encode(ct).decode("utf-8")


def decrypt_client(ciphertext_b64: str) -> str:
    ct = b64decode(ciphertext_b64)
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(IV))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ct) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    data = unpadder.update(padded_data) + unpadder.finalize()
    return data.decode("utf-8")


class OSNCollector:
    def __init__(self):
        self.channels: List[Dict[str, Any]] = []
        self.schedules: List[Dict[str, Any]] = []

    def fetch_channels(self) -> List[Dict[str, Any]]:
        print("1. Fetching official OSN channels list...")
        all_channels_map = {}
        for platform in ["Legacy", "Android"]:
            url = f"https://www.osn.com/apidata/channels?platform={platform}"
            for _ in range(3):
                try:
                    req = urllib.request.Request(url, headers=HEADERS)
                    with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
                        raw = json.loads(resp.read().decode("utf-8"))
                        if "encrypted" in raw:
                            dec = decrypt_client(raw["encrypted"])
                            ch_list = json.loads(dec)
                            for ch in ch_list:
                                guid = str(ch.get("guid") or "").strip()
                                if guid and guid not in all_channels_map:
                                    all_channels_map[guid] = ch
                            break
                except Exception:
                    time.sleep(0.3)

        print(f"✓ Found {len(all_channels_map)} official OSN channels with HD logos!")
        self.channels = list(all_channels_map.values())
        return self.channels

    def fetch_batch_schedule(self, guids_batch: List[str], start_dt: datetime, end_dt: datetime, batch_idx: int) -> List[Dict[str, Any]]:
        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)
        guids_str = "|".join(guids_batch)

        payload = {
            "channelGuid": guids_str,
            "startTime": start_ms,
            "endTime": end_ms
        }

        enc_data = encrypt_client(json.dumps(payload))
        headers = dict(HEADERS)
        headers["X-Encrypted-Data"] = enc_data

        t_param = f"batch{batch_idx}-time{start_ms}-{end_ms}-boxLegacy"
        url = f"https://www.osn.com/apidata/tv-schedule-timeline?t={t_param}"

        for _ in range(3):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                    raw = json.loads(resp.read().decode("utf-8"))
                    if "encrypted" in raw:
                        dec = decrypt_client(raw["encrypted"])
                        data = json.loads(dec)
                        if isinstance(data, dict) and "entries" in data:
                            return data["entries"]
                        elif isinstance(data, list):
                            return data
            except Exception:
                time.sleep(0.3)
        return []

    def fetch_all_schedules(self, days_ahead: int = 3) -> List[Dict[str, Any]]:
        if not self.channels:
            self.fetch_channels()

        now = datetime.now()
        start_dt = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_dt = start_dt + timedelta(days=days_ahead)

        valid_guids = [str(c["guid"]).strip() for c in self.channels if c.get("guid")]
        batch_size = 5
        batches = [valid_guids[i:i + batch_size] for i in range(0, len(valid_guids), batch_size)]

        print(f"2. Fetching live schedules for {len(valid_guids)} channels in {len(batches)} batches...")
        channel_entries = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.fetch_batch_schedule, b, start_dt, end_dt, idx + 1) for idx, b in enumerate(batches)]
            for f in concurrent.futures.as_completed(futures):
                items = f.result()
                if items:
                    channel_entries.extend(items)

        print(f"✓ Received schedule data for {len(channel_entries)} channel feeds from OSN!")

        # Format programs into standard TV Guide structure
        formatted = []
        item_id_counter = 500000

        # Build guid to channel info map
        guid_map = {str(c["guid"]).strip(): c for c in self.channels}

        for ch_entry in channel_entries:
            ch_guid = str(ch_entry.get("guid") or "").strip()
            ch_info = guid_map.get(ch_guid) or {}
            ch_name = ch_entry.get("title") or ch_info.get("title") or f"OSN Channel {ch_guid}"
            ch_logo = ch_info.get("imagePath")
            
            listings = ch_entry.get("listings") or []
            for item in listings:
                prog = item.get("program") or {}
                title_loc = prog.get("titleLocalized") or {}
                title = title_loc.get("ar") or title_loc.get("en") or prog.get("title")
                if not title:
                    continue

                desc_loc = prog.get("descriptionLocalized") or {}
                overview = desc_loc.get("ar") or desc_loc.get("en") or prog.get("description")

                thumbs = prog.get("thumbnails") or {}
                portrait = (
                    thumbs.get("portraitImage-ar", {}).get("url") or
                    thumbs.get("portraitImage-en", {}).get("url") or
                    thumbs.get("landscapeImage-ar", {}).get("url")
                )
                backdrop = (
                    thumbs.get("landscapeImage-ar", {}).get("url") or
                    thumbs.get("landscapeImage-en", {}).get("url") or
                    thumbs.get("landscapeTitleImage-ar", {}).get("url")
                )

                st_ms = item.get("startTime")
                et_ms = item.get("endTime")
                if not st_ms or not et_ms:
                    continue

                # Convert to Cairo local time (UTC+3)
                st_dt = datetime.utcfromtimestamp(st_ms / 1000) + timedelta(hours=3)
                et_dt = datetime.utcfromtimestamp(et_ms / 1000) + timedelta(hours=3)

                date_str = st_dt.strftime("%Y-%m-%d")
                start_time = st_dt.strftime("%H:%M")
                end_date_str = et_dt.strftime("%Y-%m-%d")
                end_time = et_dt.strftime("%H:%M")

                formatted.append({
                    "source": "osn_official_api",
                    "is_verified": True,
                    "osn_guid": ch_guid,
                    "channelName": ch_name,
                    "channel_logo": ch_logo,
                    "title": title,
                    "title_en": prog.get("title"),
                    "date": date_str,
                    "startTime": start_time,
                    "endTime": end_time,
                    "endDate": end_date_str,
                    "sourceItemId": f"osn_{ch_guid}_{item_id_counter}",
                    "poster": portrait,
                    "backdrop": backdrop,
                    "overview": overview,
                    "year": prog.get("year"),
                    "runtime": prog.get("runtime"),
                    "programType": prog.get("programType"),
                    "rating": prog.get("osnprogram$publicRating")
                })
                item_id_counter += 1

        self.schedules = formatted
        print(f"✓ Formatted {len(self.schedules)} verified official broadcasts from OSN!")
        return self.schedules


if __name__ == "__main__":
    collector = OSNCollector()
    channels = collector.fetch_channels()
    schedules = collector.fetch_all_schedules(days_ahead=3)
    
    out = {
        "status": "success",
        "channels_count": len(channels),
        "broadcasts_count": len(schedules),
        "channels": channels,
        "data": schedules
    }
    Path("data/osn_schedule.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("✓ Saved to data/osn_schedule.json successfully!")

