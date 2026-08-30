import base64

# =============================================================================
# TV Guide Channel Logos & Brand Styling System (115+ Channels)
# =============================================================================

CHANNEL_BRAND_STYLES = {
    # 1. Rotana Group & LBC
    "431": {"color": "#E50914", "short": "سينما KSA", "text": "روتانا سينما"},
    "439": {"color": "#DC2626", "short": "سينما مصر", "text": "روتانا سينما"},
    "437": {"color": "#F59E0B", "short": "كوميدي", "text": "روتانا كوميدي"},
    "438": {"color": "#78350F", "short": "كلاسيك", "text": "روتانا كلاسيك"},
    "436": {"color": "#7C3AED", "short": "دراما", "text": "روتانا دراما"},
    "435": {"color": "#059669", "short": "خليجية", "text": "روتانا خليجية"},
    "434": {"color": "#BE185D", "short": "LBC", "text": "إل بي سي"},
    "446": {"color": "#047857", "short": "الرسالة", "text": "قناة الرسالة"},
    "rotana_clip": {"color": "#EC4899", "short": "كليب", "text": "روتانا كليب"},

    # 2. MBC Group
    "mbc1": {"color": "#2563EB", "short": "MBC 1", "text": "إم بي سي 1"},
    "mbc2": {"color": "#D97706", "short": "MBC 2", "text": "إم بي سي 2"},
    "mbc4": {"color": "#9333EA", "short": "MBC 4", "text": "إم بي سي 4"},
    "mbc_action": {"color": "#DC2626", "short": "ACTION", "text": "MBC أكشن"},
    "mbc_max": {"color": "#0284C7", "short": "MAX", "text": "MBC ماكس"},
    "mbc_drama": {"color": "#C026D3", "short": "دراما", "text": "MBC دراما"},
    "mbc_masr": {"color": "#B91C1C", "short": "مصر", "text": "MBC مصر"},
    "mbc_masr2": {"color": "#EA580C", "short": "مصر 2", "text": "MBC مصر 2"},
    "mbc_bollywood": {"color": "#DB2777", "short": "بوليود", "text": "MBC بوليود"},
    "mbc_iraq": {"color": "#0D9488", "short": "العراق", "text": "MBC العراق"},
    "wanasa": {"color": "#F43F5E", "short": "وناسة", "text": "قناة وناسة"},

    # 3. Egyptian Television & Maspero (التلفزيون المصري وقنوات النيل)
    "aloula": {"color": "#B91C1C", "short": "الأولى", "text": "القناة الأولى المصرية"},
    "althaniya": {"color": "#1D4ED8", "short": "الثانية", "text": "القناة الثانية"},
    "almasriya": {"color": "#047857", "short": "المصرية", "text": "الفضائية المصرية"},
    "nile_cinema": {"color": "#DC2626", "short": "نايل سينما", "text": "نايل سينما"},
    "nile_drama": {"color": "#7E22CE", "short": "نايل دراما", "text": "نايل دراما"},
    "nile_comedy": {"color": "#D97706", "short": "نايل كوميدي", "text": "نايل كوميدي"},
    "nile_life": {"color": "#0284C7", "short": "نايل لايف", "text": "نايل لايف"},
    "maspero_zaman": {"color": "#854D0E", "short": "ماسبيرو", "text": "ماسبيرو زمان"},

    # 4. Egyptian Major Private Networks (الشبكات المصرية الخاصة)
    "dmc": {"color": "#2563EB", "short": "DMC", "text": "دي إم سي"},
    "dmc_drama": {"color": "#9333EA", "short": "DMC دراما", "text": "DMC دراما"},
    "on_e": {"color": "#EA580C", "short": "ON", "text": "أون إي"},
    "on_drama": {"color": "#E11D48", "short": "ON دراما", "text": "أون دراما"},
    "ontime_sports1": {"color": "#DC2626", "short": "ON TIME 1", "text": "أون تايم سبورت 1"},
    "ontime_sports2": {"color": "#B91C1C", "short": "ON TIME 2", "text": "أون تايم سبورت 2"},
    "cbc": {"color": "#DC2626", "short": "CBC", "text": "سي بي سي"},
    "cbc_drama": {"color": "#7E22CE", "short": "CBC دراما", "text": "CBC دراما"},
    "cbc_sofra": {"color": "#EA580C", "short": "سفرة", "text": "CBC سفرة"},
    "extra_news": {"color": "#1E3A8A", "short": "EXTRA", "text": "إكسترا نيوز"},
    "extra_live": {"color": "#1E40AF", "short": "LIVE", "text": "إكسترا لايف"},
    "alhayah": {"color": "#991B1B", "short": "الحياة", "text": "قناة الحياة"},
    "alhayah_drama": {"color": "#831843", "short": "الحياة D", "text": "الحياة دراما"},
    "alnahar": {"color": "#0284C7", "short": "النهار", "text": "قناة النهار"},
    "alnahar_drama": {"color": "#6D28D9", "short": "النهار D", "text": "النهار دراما"},
    "alnahar_cinema": {"color": "#DC2626", "short": "النهار C", "text": "النهار سينما"},
    "alnahar_nour": {"color": "#059669", "short": "النهار نور", "text": "النهار نور"},
    "alkahera": {"color": "#0891B2", "short": "القاهرة", "text": "القاهرة والناس"},
    "alkahera2": {"color": "#0E7490", "short": "القاهرة 2", "text": "القاهرة والناس 2"},
    "almehwar": {"color": "#4338CA", "short": "المحور", "text": "قناة المحور"},
    "almehwar_drama": {"color": "#581C87", "short": "المحور D", "text": "المحور دراما"},
    "sada_elbalad": {"color": "#B91C1C", "short": "صدى البلد", "text": "صدى البلد"},
    "sada_elbalad2": {"color": "#991B1B", "short": "صدى البلد 2", "text": "صدى البلد 2"},
    "sada_drama": {"color": "#7F1D1D", "short": "صدى D", "text": "صدى البلد دراما"},
    "alshams": {"color": "#D97706", "short": "الشمس", "text": "قناة الشمس"},
    "ten_tv": {"color": "#2563EB", "short": "TeN", "text": "قناة تن"},
    "heya_tv": {"color": "#BE185D", "short": "هي", "text": "قناة هي"},
    "azhari_tv": {"color": "#047857", "short": "أزهري", "text": "قناة أزهري"},
    "alnas_tv": {"color": "#065F46", "short": "الناس", "text": "قناة الناس"},
    "madrasetna1": {"color": "#0284C7", "short": "مدرستنا 1", "text": "مدرستنا 1"},
    "madrasetna2": {"color": "#0369A1", "short": "مدرستنا 2", "text": "مدرستنا 2"},
    "alwathaeqya": {"color": "#0D9488", "short": "الوثائقية", "text": "قناة الوثائقية المصرية"},

    # 5. ART Network
    "art_aflam1": {"color": "#B91C1C", "short": "ART 1", "text": "ART أفلام 1"},
    "art_aflam2": {"color": "#991B1B", "short": "ART 2", "text": "ART أفلام 2"},
    "art_cinema": {"color": "#E11D48", "short": "سينما", "text": "ART سينما"},
    "art_hekayat": {"color": "#7E22CE", "short": "حكايات", "text": "ART حكايات"},
    "art_hekayat2": {"color": "#6B21A8", "short": "حكايات 2", "text": "ART حكايات 2"},

    # 6. OSN Network
    "osn_movies_first": {"color": "#E11D48", "short": "FIRST", "text": "OSN Movies First"},
    "osn_movies_action": {"color": "#DC2626", "short": "ACTION", "text": "OSN Movies Action"},
    "osn_movies_hollywood": {"color": "#D97706", "short": "HOLLYWOOD", "text": "OSN Hollywood"},
    "osn_series_prime": {"color": "#6366F1", "short": "PRIME", "text": "OSN Series Prime"},
    "osn_yahala": {"color": "#F59E0B", "short": "يا هلا", "text": "OSN يا هلا"},
    "osn_yahala_aflam": {"color": "#EA580C", "short": "هلا أفلام", "text": "OSN يا هلا أفلام"},

    # 7. Nile Movie & Drama Channels
    "cima": {"color": "#B45309", "short": "سيما", "text": "قناة سيما"},
    "panorama_film": {"color": "#DC2626", "short": "بانوراما F", "text": "بانوراما فيلم"},
    "panorama_drama": {"color": "#9333EA", "short": "بانوراما D", "text": "بانوراما دراما"},
    "panorama_drama2": {"color": "#7C3AED", "short": "بانوراما 2", "text": "بانوراما دراما 2"},
    "shasha_aflam": {"color": "#C2410C", "short": "الشاشة F", "text": "الشاشة أفلام"},
    "shasha_mosalsalat": {"color": "#4338CA", "short": "الشاشة M", "text": "الشاشة مسلسلات"},
    "shasha_classic": {"color": "#854D0E", "short": "الشاشة C", "text": "الشاشة كلاسيك"},
    "family_cinema": {"color": "#0284C7", "short": "فاميلي", "text": "فاميلي سينما"},
    "family_drama": {"color": "#0D9488", "short": "فاميلي D", "text": "فاميلي دراما"},
    "cairo_cinema": {"color": "#BE123C", "short": "كايرو C", "text": "كايرو سينما"},
    "cairo_drama": {"color": "#831843", "short": "كايرو D", "text": "كايرو دراما"},
    "melody_aflam": {"color": "#E50914", "short": "ميلودي", "text": "ميلودي أفلام"},
    "toktok_cinema": {"color": "#D97706", "short": "توك توك", "text": "توك توك سينما"},
    "alyoum_cinema": {"color": "#B91C1C", "short": "اليوم F", "text": "اليوم سينما"},

    # 8. Documentary Networks
    "nat_geo_ad": {"color": "#FBBF24", "short": "NAT GEO", "text": "ناشيونال جيوغرافيك"},
    "nat_geo_wild": {"color": "#EAB308", "short": "WILD", "text": "ناشيونال جيوغرافيك وايلد"},
    "jazeera_doc": {"color": "#0284C7", "short": "وثائقية", "text": "الجزيرة الوثائقية"},
    "discovery_ar": {"color": "#2563EB", "short": "DISCOVERY", "text": "ديسكفري بالعربية"},
    "animal_planet_ar": {"color": "#16A34A", "short": "PLANET", "text": "أنيمال بلانيت"},
    "quest_arabiya": {"color": "#EA580C", "short": "QUEST", "text": "كويست عربية"},
    "bbc_doc_ar": {"color": "#B91C1C", "short": "BBC DOC", "text": "بي بي سي وثائقي"},
    "rt_doc_ar": {"color": "#0891B2", "short": "RT DOC", "text": "روسيا اليوم الوثائقية"},
    "dw_doc_ar": {"color": "#4F46E5", "short": "DW DOC", "text": "دويتشه فيله وثائقية"},

    # 9. Dubai Media
    "dubai_tv": {"color": "#0284C7", "short": "دبي", "text": "تلفزيون دبي"},
    "dubai_one": {"color": "#475569", "short": "ONE", "text": "دبي وان"},
    "sama_dubai": {"color": "#D97706", "short": "سما دبي", "text": "سما دبي"},
    "dubai_zaman": {"color": "#854D0E", "short": "زمان", "text": "دبي زمان"},

    # 10. Abu Dhabi Media
    "ad_tv": {"color": "#BE185D", "short": "أبوظبي", "text": "تلفزيون أبوظبي"},
    "emarat": {"color": "#059669", "short": "الإمارات", "text": "قناة الإمارات"},
    "ad_drama": {"color": "#7C3AED", "short": "AD دراما", "text": "أبوظبي دراما"},

    # 11. Saudi SBA Networks
    "sbc": {"color": "#0284C7", "short": "SBC", "text": "إس بي سي"},
    "saudiya": {"color": "#047857", "short": "السعودية", "text": "القناة السعودية"},
    "thikrayat": {"color": "#B45309", "short": "ذكريات", "text": "قناة ذكريات"},
    "funoon": {"color": "#F59E0B", "short": "فنون", "text": "قناة فنون"},

    # 12. Levantine & Gulf Networks
    "aljadeed": {"color": "#DC2626", "short": "الجديد", "text": "قناة الجديد"},
    "mtv_lebanon": {"color": "#1D4ED8", "short": "MTV", "text": "MTV اللبنانية"},
    "jordan_tv": {"color": "#B91C1C", "short": "الأردن", "text": "التلفزيون الأردني"},
    "kuwait_tv": {"color": "#047857", "short": "الكويت", "text": "تلفزيون الكويت"},
    "sharjah_tv": {"color": "#4F46E5", "short": "الشارقة", "text": "تلفزيون الشارقة"},

    # 13. Kids & Animation
    "spacetoon": {"color": "#EA580C", "short": "سبيستون", "text": "سبيستون"},
    "cn_arabic": {"color": "#000000", "short": "CN", "text": "كرتون نتورك"},
    "majid": {"color": "#8B5CF6", "short": "ماجد", "text": "قناة ماجد"},

    # 14. News
    "alarabiya": {"color": "#831843", "short": "العربية", "text": "قناة العربية"},
    "skynews_ar": {"color": "#BE123C", "short": "SKY NEWS", "text": "سكاي نيوز عربية"},

    # 15. Zee Networks
    "zee_alwan": {"color": "#D97706", "short": "زي ألوان", "text": "زي ألوان"},
    "zee_aflam": {"color": "#DC2626", "short": "زي أفلام", "text": "زي أفلام"}
}


def get_channel_badge_svg(src_id, name_ar):
    style = CHANNEL_BRAND_STYLES.get(src_id, {"color": "#E50914", "short": name_ar[:4], "text": name_ar})
    short = style.get("short", name_ar[:4])
    color = style.get("color", "#E50914")
    
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="0 0 120 120">
  <defs>
    <linearGradient id="grad_{src_id}" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{color}" />
      <stop offset="100%" stop-color="#0F172A" stop-opacity="0.95" />
    </linearGradient>
  </defs>
  <rect width="120" height="120" rx="26" fill="url(#grad_{src_id})" stroke="rgba(255,255,255,0.2)" stroke-width="2"/>
  <text x="60" y="66" font-family="Cairo, Arial, sans-serif" font-weight="900" font-size="20" fill="#ffffff" text-anchor="middle" dominant-baseline="middle">{short}</text>
</svg>"""
    
    b64 = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{b64}"
