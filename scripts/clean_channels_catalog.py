import re

DELETED_IDS = {91, 203, 204, 216, 217, 234, 235, 236, 238, 239, 240, 241}

file_path = "collectors/channels_catalog.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Pattern to match each channel dict inside ALL_CHANNELS_CATALOG
# e.g.:
#     {
#         "category": ...
#         "id": 238,
#         ...
#     },?
def filter_channels():
    import sys
    sys.path.insert(0, ".")
    from collectors.channels_catalog import ALL_CHANNELS_CATALOG
    remaining = [ch for ch in ALL_CHANNELS_CATALOG if ch.get("id") not in DELETED_IDS]
    print(f"ALL_CHANNELS_CATALOG: {len(ALL_CHANNELS_CATALOG)} -> {len(remaining)}")

    # Reformat ALL_CHANNELS_CATALOG in collectors/channels_catalog.py
    import pprint
    new_code = "ALL_CHANNELS_CATALOG = [\n"
    for ch in remaining:
        new_code += "    {\n"
        for k, v in ch.items():
            new_code += f"        {repr(k)}: {repr(v)},\n"
        new_code += "    },\n"
    new_code += "]\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_code)
    print("Updated collectors/channels_catalog.py successfully")

filter_channels()

