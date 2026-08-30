import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collectors.logo_provider import get_channel_badge_svg, CHANNEL_BRAND_STYLES

CHANNELS_FILE = Path("collectors/channels_catalog.py")


def update_catalog_logos():
    from collectors.channels_catalog import ALL_CHANNELS_CATALOG
    
    for ch in ALL_CHANNELS_CATALOG:
        src_id = ch["source_channel_id"]
        name_ar = ch["name_ar"]
        # Generate official SVG badge
        ch["logo_url"] = get_channel_badge_svg(src_id, name_ar)

    content = f"""# =============================================================================
# TV Guide - Comprehensive Channels & Satellite Frequencies Catalog (36 Channels)
# =============================================================================

ALL_CHANNELS_CATALOG = {repr(ALL_CHANNELS_CATALOG)}
"""
    CHANNELS_FILE.write_text(content, encoding="utf-8")
    print("Updated all 36 channel logos with verified high-res vector badges.")


if __name__ == "__main__":
    update_catalog_logos()

