import json
import re

print("=" * 80)
print("FIXING USER ISSUES: PADEL TIME, OSN MOVIES, AND PLACEHOLDER TITLES")
print("=" * 80)

# -----------------------------------------------------------------------------
# 1. PERMANENTLY DELETE PADEL TIME (ID 179)
# -----------------------------------------------------------------------------
channels = json.load(open("data/channels.json", encoding="utf-8"))
channels = [ch for ch in channels if ch["id"] != 179 and "padel" not in str(ch).lower()]
print(f"Channels after deleting Padel Time: {len(channels)}")

# -----------------------------------------------------------------------------
# 2. PROPERLY DEFINE OSN MOVIES PAID CHANNELS (10225, 10301, 15666, 15669)
# -----------------------------------------------------------------------------
osn_missing_channels = [
    {
        "id": 10301,
        "name": "OSN Movies Premiere",
        "name_ar": "OSN Movies Premiere",
        "name_en": "OSN Movies Premiere",
        "displayName": "OSN Movies Premiere",
        "category": "movies",
        "country": "UAE",
        "language": "English/Arabic",
        "logo_url": "https://images.tv.osn.com/colossus/images/channel_logos/v4/OSN-Movies-Premiere_ATV.png",
        "is_paid": True,
        "is_encrypted": True,
        "primaryContentType": "movie",
        "classificationConfidence": 1.0,
        "classificationSource": "MANUAL_VERIFIED"
    },
    {
        "id": 15666,
        "name": "OSN Movies Pop Up",
        "name_ar": "OSN Movies Pop Up",
        "name_en": "OSN Movies Pop Up",
        "displayName": "OSN Movies Pop Up",
        "category": "movies",
        "country": "UAE",
        "language": "English/Arabic",
        "logo_url": "https://images.tv.osn.com/colossus/images/channel_logos/v4/OSN-Movies-Pop-Up_ATV.png",
        "is_paid": True,
        "is_encrypted": True,
        "primaryContentType": "movie",
        "classificationConfidence": 1.0,
        "classificationSource": "MANUAL_VERIFIED"
    },
    {
        "id": 10225,
        "name": "OSN Movies Action",
        "name_ar": "OSN Movies Action",
        "name_en": "OSN Movies Action",
        "displayName": "OSN Movies Action",
        "category": "movies",
        "country": "UAE",
        "language": "English/Arabic",
        "logo_url": "https://images.tv.osn.com/colossus/images/channel_logos/v4/OSN-Movies-Action_ATV.png",
        "is_paid": True,
        "is_encrypted": True,
        "primaryContentType": "movie",
        "classificationConfidence": 1.0,
        "classificationSource": "MANUAL_VERIFIED"
    },
    {
        "id": 15669,
        "name": "OSN Movies Comedy",
        "name_ar": "OSN Movies Comedy",
        "name_en": "OSN Movies Comedy",
        "displayName": "OSN Movies Comedy",
        "category": "movies",
        "country": "UAE",
        "language": "English/Arabic",
        "logo_url": "https://images.tv.osn.com/colossus/images/channel_logos/v4/OSN-Movies-Comedy_ATV.png",
        "is_paid": True,
        "is_encrypted": True,
        "primaryContentType": "movie",
        "classificationConfidence": 1.0,
        "classificationSource": "MANUAL_VERIFIED"
    }
]

# Add to channels if not present
existing_ids = {ch["id"] for ch in channels}
for oc in osn_missing_channels:
    if oc["id"] not in existing_ids:
        channels.append(oc)
print(f"Channels after adding OSN Movies paid channels: {len(channels)}")

# Save updated channels.json
with open("data/channels.json", "w", encoding="utf-8") as f:
    json.dump(channels, f, ensure_ascii=False, indent=2)
with open("android/app/src/main/assets/channels.json", "w", encoding="utf-8") as f:
    json.dump(channels, f, ensure_ascii=False, indent=2)

# Build channel name lookup
channel_name_map = {}
for ch in channels:
    cname = ch.get("displayName") or ch.get("name_ar") or ch.get("name") or "القناة"
    # remove prefix "قناة" if present for cleaner names
    cname_clean = re.sub(r"^قناة\s+", "", cname).strip()
    channel_name_map[ch["id"]] = cname_clean

# -----------------------------------------------------------------------------
# 3. FIX SCHEDULES: PURGE PADEL TIME, FIX PLACEHOLDER TITLES & MERGE FILLERS
# -----------------------------------------------------------------------------
scheds_data = json.load(open("data/schedules.json", encoding="utf-8"))
is_dict = isinstance(scheds_data, dict) and "schedules" in scheds_data
scheds = scheds_data["schedules"] if is_dict else scheds_data

# Filter out Padel Time (179)
scheds = [s for s in scheds if s.get("channelId") != 179]

# Group by (channelId, date) for contiguous processing and merging
scheds_by_channel_date = {}
for s in scheds:
    key = (s.get("channelId"), s.get("date"))
    scheds_by_channel_date.setdefault(key, []).append(s)

fixed_schedules = []
merged_fillers_count = 0
fixed_titles_count = 0

for (cid, date), day_scheds in scheds_by_channel_date.items():
    # Sort by start_time
    day_scheds.sort(key=lambda x: x.get("startTime", ""))
    
    ch_clean_name = channel_name_map.get(cid, "القناة")
    
    # 1. Normalize individual placeholders first
    for s in day_scheds:
        title = (s.get("title") or "").strip()
        st = s.get("startTime", "")
        
        # A. Fix "رقم 10"
        if title == "رقم 10" and cid in (21, 23):
            s["title"] = "برنامج رقم 10 (رياضي)"
            s["programType"] = "sports"
            s["title_en"] = "Number 10 Sports Show"
            fixed_titles_count += 1
            
        # B. Fix "عربي"
        elif title == "عربي":
            # If late night (23:00 to 04:00): Arabic movie
            if st >= "23:00" or st < "04:00":
                s["title"] = "فيلم عربي"
                s["programType"] = "movie"
                s["title_en"] = "Arabic Movie"
            else:
                s["title"] = f"منوعات {ch_clean_name}"
                s["programType"] = "other"
                s["title_en"] = f"{ch_clean_name} Variety"
            fixed_titles_count += 1
            
        # C. Fix generic "برنامج تلفزيوني" / "برنامج تليفزيوني"
        elif title in ("برنامج تلفزيوني", "برنامج تليفزيوني"):
            if st >= "00:00" and st < "07:00":
                if cid in (60, 61):  # ART حكايات
                    s["title"] = "إعادة دراما الليل"
                    s["programType"] = "series"
                else:
                    s["title"] = "فترة بث ليلي / إعادة برامج"
                    s["programType"] = "other"
            else:
                s["title"] = f"برامج {ch_clean_name}"
                s["programType"] = "other"
            s["title_en"] = f"{ch_clean_name} Programming"
            fixed_titles_count += 1

    # 2. Merge consecutive identical late-night filler schedules
    # (e.g. 5 consecutive 1-hour "فترة بث ليلي / إعادة برامج" -> one block from 02:00 to 07:00)
    merged_day_scheds = []
    i = 0
    while i < len(day_scheds):
        curr = day_scheds[i]
        curr_title = curr.get("title", "")
        
        # Check if it's a filler that can be merged with subsequent identical fillers
        if curr_title in ("فترة بث ليلي / إعادة برامج", "إعادة دراما الليل"):
            j = i + 1
            last_end = curr.get("endTime")
            while j < len(day_scheds):
                nxt = day_scheds[j]
                if nxt.get("title") == curr_title and nxt.get("startTime") == last_end:
                    last_end = nxt.get("endTime")
                    j += 1
                else:
                    break
            
            if j > i + 1:
                # Merged block
                curr["endTime"] = last_end
                merged_fillers_count += (j - i - 1)
                merged_day_scheds.append(curr)
                i = j
                continue
                
        merged_day_scheds.append(curr)
        i += 1
        
    fixed_schedules.extend(merged_day_scheds)

print(f"Fixed titles count: {fixed_titles_count}")
print(f"Merged filler slots count: {merged_fillers_count}")
print(f"Total schedules: {len(scheds)} -> {len(fixed_schedules)}")

# Save updated schedules.json
if is_dict:
    scheds_data["schedules"] = fixed_schedules
    out_data = scheds_data
else:
    out_data = fixed_schedules

with open("data/schedules.json", "w", encoding="utf-8") as f:
    json.dump(out_data, f, ensure_ascii=False, indent=2)

print("Saved updated data/schedules.json")
