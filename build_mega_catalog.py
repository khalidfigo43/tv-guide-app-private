import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from collectors.logo_provider import get_channel_badge_svg

CHANNELS_DATA_FULL = [
    # =========================================================================
    # 1. ROTANA GROUP & LBC (9 Channels)
    # =========================================================================
    {"id": 1, "name_ar": "روتانا سينما السعودية", "name_en": "Rotana Cinema KSA", "src": "rotana", "src_id": "431", "cat": "movies", "c": "SA", "nile": "12226 H 27500", "arab": "11843 H 27500"},
    {"id": 2, "name_ar": "روتانا سينما مصر", "name_en": "Rotana Cinema Egypt", "src": "rotana", "src_id": "439", "cat": "movies", "c": "EG", "nile": "12226 H 27500", "arab": "11843 H 27500"},
    {"id": 3, "name_ar": "روتانا كوميدي", "name_en": "Rotana Comedy", "src": "rotana", "src_id": "437", "cat": "comedy", "c": "SA", "nile": "12226 H 27500", "arab": "11843 H 27500"},
    {"id": 4, "name_ar": "روتانا كلاسيك", "name_en": "Rotana Classic", "src": "rotana", "src_id": "438", "cat": "classic", "c": "SA", "nile": "12226 H 27500", "arab": "11843 H 27500"},
    {"id": 5, "name_ar": "روتانا دراما", "name_en": "Rotana Drama", "src": "rotana", "src_id": "436", "cat": "drama", "c": "SA", "nile": "12226 H 27500", "arab": "11843 H 27500"},
    {"id": 6, "name_ar": "روتانا خليجية", "name_en": "Rotana Khaleejiya", "src": "rotana", "src_id": "435", "cat": "variety", "c": "SA", "nile": "12226 H 27500", "arab": "11843 H 27500"},
    {"id": 7, "name_ar": "إل بي سي", "name_en": "LBC Sat", "src": "rotana", "src_id": "434", "cat": "general", "c": "LB", "nile": "12226 H 27500", "arab": "11843 H 27500"},
    {"id": 8, "name_ar": "الرسالة", "name_en": "Al Resalah", "src": "rotana", "src_id": "446", "cat": "religious", "c": "SA", "nile": "12226 H 27500", "arab": "11843 H 27500"},
    {"id": 9, "name_ar": "روتانا كليب", "name_en": "Rotana Clip", "src": "rotana", "src_id": "rotana_clip", "cat": "music", "c": "SA", "nile": "12226 H 27500", "arab": "11843 H 27500"},

    # =========================================================================
    # 2. MBC GROUP (11 Channels)
    # =========================================================================
    {"id": 10, "name_ar": "إم بي سي 1", "name_en": "MBC 1", "src": "mbc", "src_id": "mbc1", "cat": "general", "c": "SA", "nile": "11470 V 27500", "arab": "11270 V 27500"},
    {"id": 11, "name_ar": "إم بي سي 2", "name_en": "MBC 2", "src": "mbc", "src_id": "mbc2", "cat": "movies", "c": "SA", "nile": "11470 V 27500", "arab": "11270 V 27500"},
    {"id": 12, "name_ar": "إم بي سي 4", "name_en": "MBC 4", "src": "mbc", "src_id": "mbc4", "cat": "series", "c": "SA", "nile": "11470 V 27500", "arab": "11270 V 27500"},
    {"id": 13, "name_ar": "إم بي سي أكشن", "name_en": "MBC Action", "src": "mbc", "src_id": "mbc_action", "cat": "action", "c": "SA", "nile": "11470 V 27500", "arab": "11270 V 27500"},
    {"id": 14, "name_ar": "إم بي سي ماكس", "name_en": "MBC Max", "src": "mbc", "src_id": "mbc_max", "cat": "movies", "c": "SA", "nile": "11470 V 27500", "arab": "11270 V 27500"},
    {"id": 15, "name_ar": "إم بي سي دراما", "name_en": "MBC Drama", "src": "mbc", "src_id": "mbc_drama", "cat": "drama", "c": "SA", "nile": "11470 V 27500", "arab": "11270 V 27500"},
    {"id": 16, "name_ar": "إم بي سي مصر", "name_en": "MBC Masr", "src": "mbc", "src_id": "mbc_masr", "cat": "general", "c": "EG", "nile": "12015 V 27500", "arab": "11270 V 27500"},
    {"id": 17, "name_ar": "إم بي سي مصر 2", "name_en": "MBC Masr 2", "src": "mbc", "src_id": "mbc_masr2", "cat": "general", "c": "EG", "nile": "11823 V 27500", "arab": None},
    {"id": 18, "name_ar": "إم بي سي بوليود", "name_en": "MBC Bollywood", "src": "mbc", "src_id": "mbc_bollywood", "cat": "bollywood", "c": "SA", "nile": "11470 V 27500", "arab": None},
    {"id": 19, "name_ar": "إم بي سي العراق", "name_en": "MBC Iraq", "src": "mbc", "src_id": "mbc_iraq", "cat": "general", "c": "IQ", "nile": "12226 H 27500", "arab": "11862 V 27500"},
    {"id": 20, "name_ar": "قناة وناسة", "name_en": "Wanasa TV", "src": "mbc", "src_id": "wanasa", "cat": "kids", "c": "SA", "nile": "11470 V 27500", "arab": "11270 V 27500"},

    # =========================================================================
    # 3. EGYPTIAN NATIONAL & MASPERO (التلفزيون المصري وقنوات النيل) (8 Channels)
    # =========================================================================
    {"id": 21, "name_ar": "القناة الأولى المصرية", "name_en": "Al Oula Egypt", "src": "egypt_maspero", "src_id": "aloula", "cat": "general", "c": "EG", "nile": "11766 H 27500", "arab": "12054 V 27500"},
    {"id": 22, "name_ar": "القناة الثانية المصرية", "name_en": "Al Thaniya Egypt", "src": "egypt_maspero", "src_id": "althaniya", "cat": "general", "c": "EG", "nile": "11766 H 27500", "arab": None},
    {"id": 23, "name_ar": "الفضائية المصرية", "name_en": "Al Masriya", "src": "egypt_maspero", "src_id": "almasriya", "cat": "general", "c": "EG", "nile": "11766 H 27500", "arab": "12054 V 27500"},
    {"id": 24, "name_ar": "نايل سينما", "name_en": "Nile Cinema", "src": "egypt_maspero", "src_id": "nile_cinema", "cat": "movies", "c": "EG", "nile": "11843 H 27500", "arab": None},
    {"id": 25, "name_ar": "نايل دراما", "name_en": "Nile Drama", "src": "egypt_maspero", "src_id": "nile_drama", "cat": "drama", "c": "EG", "nile": "11843 H 27500", "arab": None},
    {"id": 26, "name_ar": "نايل كوميدي", "name_en": "Nile Comedy", "src": "egypt_maspero", "src_id": "nile_comedy", "cat": "comedy", "c": "EG", "nile": "11843 H 27500", "arab": None},
    {"id": 27, "name_ar": "نايل لايف", "name_en": "Nile Life", "src": "egypt_maspero", "src_id": "nile_life", "cat": "variety", "c": "EG", "nile": "11843 H 27500", "arab": None},
    {"id": 28, "name_ar": "ماسبيرو زمان", "name_en": "Maspero Zaman", "src": "egypt_maspero", "src_id": "maspero_zaman", "cat": "classic", "c": "EG", "nile": "11843 H 27500", "arab": None},

    # =========================================================================
    # 4. EGYPTIAN MAJOR PRIVATE NETWORKS (الشبكات المصرية الكبرى) (24 Channels)
    # =========================================================================
    {"id": 29, "name_ar": "دي إم سي", "name_en": "DMC", "src": "egypt", "src_id": "dmc", "cat": "general", "c": "EG", "nile": "12092 V 27500", "arab": None},
    {"id": 30, "name_ar": "دي إم سي دراما", "name_en": "DMC Drama", "src": "egypt", "src_id": "dmc_drama", "cat": "drama", "c": "EG", "nile": "12092 V 27500", "arab": None},
    {"id": 31, "name_ar": "أون إي", "name_en": "ON E", "src": "egypt", "src_id": "on_e", "cat": "general", "c": "EG", "nile": "11862 V 27500", "arab": None},
    {"id": 32, "name_ar": "أون دراما", "name_en": "ON Drama", "src": "egypt", "src_id": "on_drama", "cat": "drama", "c": "EG", "nile": "11862 V 27500", "arab": None},
    {"id": 33, "name_ar": "أون تايم سبورت 1", "name_en": "ON Time Sports 1", "src": "egypt", "src_id": "ontime_sports1", "cat": "sports", "c": "EG", "nile": "11862 V 27500", "arab": None},
    {"id": 34, "name_ar": "أون تايم سبورت 2", "name_en": "ON Time Sports 2", "src": "egypt", "src_id": "ontime_sports2", "cat": "sports", "c": "EG", "nile": "11862 V 27500", "arab": None},
    {"id": 35, "name_ar": "سي بي سي", "name_en": "CBC", "src": "egypt", "src_id": "cbc", "cat": "general", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 36, "name_ar": "سي بي سي دراما", "name_en": "CBC Drama", "src": "egypt", "src_id": "cbc_drama", "cat": "drama", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 37, "name_ar": "سي بي سي سفرة", "name_en": "CBC Sofra", "src": "egypt", "src_id": "cbc_sofra", "cat": "lifestyle", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 38, "name_ar": "إكسترا نيوز", "name_en": "Extra News", "src": "egypt", "src_id": "extra_news", "cat": "news", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 39, "name_ar": "إكسترا لايف", "name_en": "Extra Live", "src": "egypt", "src_id": "extra_live", "cat": "news", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 40, "name_ar": "قناة الحياة", "name_en": "Al Hayah", "src": "egypt", "src_id": "alhayah", "cat": "general", "c": "EG", "nile": "12206 V 27500", "arab": None},
    {"id": 41, "name_ar": "الحياة دراما", "name_en": "Al Hayah Drama", "src": "egypt", "src_id": "alhayah_drama", "cat": "drama", "c": "EG", "nile": "12206 V 27500", "arab": None},
    {"id": 42, "name_ar": "قناة النهار", "name_en": "Al Nahar", "src": "egypt", "src_id": "alnahar", "cat": "general", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 43, "name_ar": "النهار دراما", "name_en": "Al Nahar Drama", "src": "egypt", "src_id": "alnahar_drama", "cat": "drama", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 44, "name_ar": "النهار سينما", "name_en": "Al Nahar Cinema", "src": "egypt", "src_id": "alnahar_cinema", "cat": "movies", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 45, "name_ar": "النهار نور", "name_en": "Al Nahar Nour", "src": "egypt", "src_id": "alnahar_nour", "cat": "religious", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 46, "name_ar": "القاهرة والناس", "name_en": "Al Kahera Wal Nas", "src": "egypt", "src_id": "alkahera", "cat": "general", "c": "EG", "nile": "11766 H 27500", "arab": None},
    {"id": 47, "name_ar": "القاهرة والناس 2", "name_en": "Al Kahera Wal Nas 2", "src": "egypt", "src_id": "alkahera2", "cat": "general", "c": "EG", "nile": "11766 H 27500", "arab": None},
    {"id": 48, "name_ar": "قناة المحور", "name_en": "Al Mehwar", "src": "egypt", "src_id": "almehwar", "cat": "general", "c": "EG", "nile": "11823 V 27500", "arab": None},
    {"id": 49, "name_ar": "المحور دراما", "name_en": "Al Mehwar Drama", "src": "egypt", "src_id": "almehwar_drama", "cat": "drama", "c": "EG", "nile": "11823 V 27500", "arab": None},
    {"id": 50, "name_ar": "صدى البلد", "name_en": "Sada El Balad", "src": "egypt", "src_id": "sada_elbalad", "cat": "general", "c": "EG", "nile": "11823 V 27500", "arab": None},
    {"id": 51, "name_ar": "صدى البلد 2", "name_en": "Sada El Balad 2", "src": "egypt", "src_id": "sada_elbalad2", "cat": "general", "c": "EG", "nile": "11823 V 27500", "arab": None},
    {"id": 52, "name_ar": "قناة الشمس", "name_en": "Al Shams", "src": "egypt", "src_id": "alshams", "cat": "general", "c": "EG", "nile": "12054 V 27500", "arab": None},
    {"id": 53, "name_ar": "قناة تن", "name_en": "TeN TV", "src": "egypt", "src_id": "ten_tv", "cat": "general", "c": "EG", "nile": "11843 H 27500", "arab": None},
    {"id": 54, "name_ar": "قناة هي", "name_en": "Heya TV", "src": "egypt", "src_id": "heya_tv", "cat": "lifestyle", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 55, "name_ar": "قناة الناس", "name_en": "Al Nas", "src": "egypt", "src_id": "alnas_tv", "cat": "religious", "c": "EG", "nile": "12054 V 27500", "arab": None},
    {"id": 56, "name_ar": "مدرستنا 1", "name_en": "Madrasetna 1", "src": "egypt", "src_id": "madrasetna1", "cat": "education", "c": "EG", "nile": "12303 H 27500", "arab": None},

    # =========================================================================
    # 5. ART NETWORK (5 Channels)
    # =========================================================================
    {"id": 57, "name_ar": "ART أفلام 1", "name_en": "ART Aflam 1", "src": "art", "src_id": "art_aflam1", "cat": "movies", "c": "SA", "nile": "12034 H 27500", "arab": "12341 H 27500"},
    {"id": 58, "name_ar": "ART أفلام 2", "name_en": "ART Aflam 2", "src": "art", "src_id": "art_aflam2", "cat": "movies", "c": "SA", "nile": "12034 H 27500", "arab": "12341 H 27500"},
    {"id": 59, "name_ar": "ART سينما", "name_en": "ART Cinema", "src": "art", "src_id": "art_cinema", "cat": "movies", "c": "SA", "nile": "12034 H 27500", "arab": "12341 H 27500"},
    {"id": 60, "name_ar": "ART حكايات", "name_en": "ART Hekayat", "src": "art", "src_id": "art_hekayat", "cat": "drama", "c": "SA", "nile": "12034 H 27500", "arab": "12341 H 27500"},
    {"id": 61, "name_ar": "ART حكايات 2", "name_en": "ART Hekayat 2", "src": "art", "src_id": "art_hekayat2", "cat": "drama", "c": "SA", "nile": "12034 H 27500", "arab": "12341 H 27500"},

    # =========================================================================
    # 6. OSN NETWORK (6 Channels)
    # =========================================================================
    {"id": 62, "name_ar": "OSN Movies First", "name_en": "OSN Movies First", "src": "osn", "src_id": "osn_movies_first", "cat": "movies", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 63, "name_ar": "OSN Movies Action", "name_en": "OSN Movies Action", "src": "osn", "src_id": "osn_movies_action", "cat": "action", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 64, "name_ar": "OSN Hollywood", "name_en": "OSN Movies Hollywood", "src": "osn", "src_id": "osn_movies_hollywood", "cat": "movies", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 65, "name_ar": "OSN Series Prime", "name_en": "OSN Series Prime", "src": "osn", "src_id": "osn_series_prime", "cat": "series", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 66, "name_ar": "OSN يا هلا", "name_en": "OSN Yahala", "src": "osn", "src_id": "osn_yahala", "cat": "drama", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 67, "name_ar": "OSN يا هلا أفلام", "name_en": "OSN Yahala Aflam", "src": "osn", "src_id": "osn_yahala_aflam", "cat": "movies", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},

    # =========================================================================
    # 7. NILESAT CINEMA & DRAMA CHANNELS (15 Channels)
    # =========================================================================
    {"id": 68, "name_ar": "قناة سيما", "name_en": "Cima TV", "src": "nile_cine", "src_id": "cima", "cat": "classic", "c": "EG", "nile": "12034 H 27500", "arab": None},
    {"id": 69, "name_ar": "بانوراما فيلم", "name_en": "Panorama Film", "src": "nile_cine", "src_id": "panorama_film", "cat": "movies", "c": "EG", "nile": "11257 H 27500", "arab": None},
    {"id": 70, "name_ar": "بانوراما دراما", "name_en": "Panorama Drama", "src": "nile_cine", "src_id": "panorama_drama", "cat": "drama", "c": "EG", "nile": "12341 H 27500", "arab": None},
    {"id": 71, "name_ar": "بانوراما دراما 2", "name_en": "Panorama Drama 2", "src": "nile_cine", "src_id": "panorama_drama2", "cat": "drama", "c": "EG", "nile": "12341 H 27500", "arab": None},
    {"id": 72, "name_ar": "الشاشة أفلام", "name_en": "Al Shasha Aflam", "src": "nile_cine", "src_id": "shasha_aflam", "cat": "movies", "c": "EG", "nile": "12562 V 27500", "arab": None},
    {"id": 73, "name_ar": "الشاشة مسلسلات", "name_en": "Al Shasha Mosalsalat", "src": "nile_cine", "src_id": "shasha_mosalsalat", "cat": "drama", "c": "EG", "nile": "12562 V 27500", "arab": None},
    {"id": 74, "name_ar": "الشاشة كلاسيك", "name_en": "Al Shasha Classic", "src": "nile_cine", "src_id": "shasha_classic", "cat": "classic", "c": "EG", "nile": "12562 V 27500", "arab": None},
    {"id": 75, "name_ar": "فاميلي سينما", "name_en": "Family Cinema", "src": "nile_cine", "src_id": "family_cinema", "cat": "movies", "c": "EG", "nile": "12562 V 27500", "arab": None},
    {"id": 76, "name_ar": "فاميلي دراما", "name_en": "Family Drama", "src": "nile_cine", "src_id": "family_drama", "cat": "drama", "c": "EG", "nile": "12562 V 27500", "arab": None},
    {"id": 77, "name_ar": "كايرو سينما", "name_en": "Cairo Cinema", "src": "nile_cine", "src_id": "cairo_cinema", "cat": "movies", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 78, "name_ar": "كايرو دراما", "name_en": "Cairo Drama", "src": "nile_cine", "src_id": "cairo_drama", "cat": "drama", "c": "EG", "nile": "11785 V 27500", "arab": None},
    {"id": 79, "name_ar": "صدى البلد دراما", "name_en": "Sada El Balad Drama", "src": "nile_cine", "src_id": "sada_drama", "cat": "drama", "c": "EG", "nile": "11823 V 27500", "arab": None},
    {"id": 80, "name_ar": "ميلودي أفلام", "name_en": "Melody Aflam", "src": "nile_cine", "src_id": "melody_aflam", "cat": "movies", "c": "EG", "nile": "11526 H 27500", "arab": None},
    {"id": 81, "name_ar": "توك توك سينما", "name_en": "TokTok Cinema", "src": "nile_cine", "src_id": "toktok_cinema", "cat": "comedy", "c": "EG", "nile": "11526 H 27500", "arab": None},
    {"id": 82, "name_ar": "اليوم سينما", "name_en": "Alyoum Cinema", "src": "nile_cine", "src_id": "alyoum_cinema", "cat": "movies", "c": "EG", "nile": "12604 H 27500", "arab": None},

    # =========================================================================
    # 8. DOCUMENTARY NETWORKS (10 Channels)
    # =========================================================================
    {"id": 83, "name_ar": "ناشيونال جيوغرافيك", "name_en": "National Geographic AD", "src": "doc", "src_id": "nat_geo_ad", "cat": "documentary", "c": "AE", "nile": "11411 H 30000", "arab": "11804 H 27500"},
    {"id": 84, "name_ar": "ناشيونال جيوغرافيك وايلد", "name_en": "Nat Geo Wild", "src": "doc", "src_id": "nat_geo_wild", "cat": "documentary", "c": "AE", "nile": "11411 H 30000", "arab": "11804 H 27500"},
    {"id": 85, "name_ar": "الجزيرة الوثائقية", "name_en": "Al Jazeera Documentary", "src": "doc", "src_id": "jazeera_doc", "cat": "documentary", "c": "QA", "nile": "10971 V 27500", "arab": "11604 H 27500"},
    {"id": 86, "name_ar": "قناة الوثائقية المصرية", "name_en": "Al Wathaeqya", "src": "doc", "src_id": "alwathaeqya", "cat": "documentary", "c": "EG", "nile": "12303 H 27500", "arab": None},
    {"id": 87, "name_ar": "ديسكفري بالعربية", "name_en": "Discovery Channel Arabic", "src": "doc", "src_id": "discovery_ar", "cat": "documentary", "c": "US", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 88, "name_ar": "أنيمال بلانيت", "name_en": "Animal Planet Arabic", "src": "doc", "src_id": "animal_planet_ar", "cat": "documentary", "c": "US", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 89, "name_ar": "كويست عربية", "name_en": "Quest Arabiya", "src": "doc", "src_id": "quest_arabiya", "cat": "documentary", "c": "AE", "nile": "11785 V 27500", "arab": "12130 V 27500"},
    {"id": 90, "name_ar": "بي بي سي وثائقي", "name_en": "BBC Arabic Documentaries", "src": "doc", "src_id": "bbc_doc_ar", "cat": "documentary", "c": "GB", "nile": "11564 H 27500", "arab": "11996 H 27500"},
    {"id": 91, "name_ar": "روسيا اليوم الوثائقية", "name_en": "RT Arabic Documentary", "src": "doc", "src_id": "rt_doc_ar", "cat": "documentary", "c": "RU", "nile": "10892 H 27500", "arab": "11747 V 27500"},
    {"id": 92, "name_ar": "دويتشه فيله وثائقية", "name_en": "DW Documentary Arabic", "src": "doc", "src_id": "dw_doc_ar", "cat": "documentary", "c": "DE", "nile": "11137 H 27500", "arab": "11900 V 27500"},

    # =========================================================================
    # 9. DUBAI & ABU DHABI MEDIA (7 Channels)
    # =========================================================================
    {"id": 93, "name_ar": "تلفزيون دبي", "name_en": "Dubai TV", "src": "dubai", "src_id": "dubai_tv", "cat": "general", "c": "AE", "nile": "12418 H 27500", "arab": "12130 V 27500"},
    {"id": 94, "name_ar": "دبي وان", "name_en": "Dubai One", "src": "dubai", "src_id": "dubai_one", "cat": "movies", "c": "AE", "nile": "12418 H 27500", "arab": "12130 V 27500"},
    {"id": 95, "name_ar": "سما دبي", "name_en": "Sama Dubai", "src": "dubai", "src_id": "sama_dubai", "cat": "variety", "c": "AE", "nile": "12418 H 27500", "arab": "12130 V 27500"},
    {"id": 96, "name_ar": "دبي زمان", "name_en": "Dubai Zaman", "src": "dubai", "src_id": "dubai_zaman", "cat": "classic", "c": "AE", "nile": "12418 H 27500", "arab": "12130 V 27500"},
    {"id": 97, "name_ar": "تلفزيون أبوظبي", "name_en": "Abu Dhabi TV", "src": "admedia", "src_id": "ad_tv", "cat": "general", "c": "AE", "nile": "11411 H 30000", "arab": "11804 H 27500"},
    {"id": 98, "name_ar": "قناة الإمارات", "name_en": "Emarat TV", "src": "admedia", "src_id": "emarat", "cat": "general", "c": "AE", "nile": "11411 H 30000", "arab": "11804 H 27500"},
    {"id": 99, "name_ar": "أبوظبي دراما", "name_en": "Abu Dhabi Drama", "src": "admedia", "src_id": "ad_drama", "cat": "drama", "c": "AE", "nile": "11411 H 30000", "arab": "11804 H 27500"},

    # =========================================================================
    # 10. SAUDI SBA & GULF (6 Channels)
    # =========================================================================
    {"id": 100, "name_ar": "إس بي سي", "name_en": "SBC", "src": "sba", "src_id": "sbc", "cat": "entertainment", "c": "SA", "nile": "12149 H 27500", "arab": "12015 V 27500"},
    {"id": 101, "name_ar": "القناة السعودية", "name_en": "Al Saudiya", "src": "sba", "src_id": "saudiya", "cat": "general", "c": "SA", "nile": "12149 H 27500", "arab": "12015 V 27500"},
    {"id": 102, "name_ar": "قناة ذكريات", "name_en": "Thikrayat", "src": "sba", "src_id": "thikrayat", "cat": "classic", "c": "SA", "nile": "12149 H 27500", "arab": "12015 V 27500"},
    {"id": 103, "name_ar": "قناة فنون", "name_en": "Funoon TV", "src": "gulf", "src_id": "funoon", "cat": "comedy", "c": "KW", "nile": "12688 V 27500", "arab": None},
    {"id": 104, "name_ar": "تلفزيون الكويت", "name_en": "Kuwait TV", "src": "gulf", "src_id": "kuwait_tv", "cat": "general", "c": "KW", "nile": "11054 V 27500", "arab": "12523 H 27500"},
    {"id": 105, "name_ar": "تلفزيون الشارقة", "name_en": "Sharjah TV", "src": "gulf", "src_id": "sharjah_tv", "cat": "general", "c": "AE", "nile": "11012 V 27500", "arab": "11862 V 27500"},

    # =========================================================================
    # 11. LEVANTINE & ARAB (3 Channels)
    # =========================================================================
    {"id": 106, "name_ar": "قناة الجديد", "name_en": "Al Jadeed", "src": "levant", "src_id": "aljadeed", "cat": "general", "c": "LB", "nile": "12188 H 27500", "arab": None},
    {"id": 107, "name_ar": "MTV اللبنانية", "name_en": "MTV Lebanon", "src": "levant", "src_id": "mtv_lebanon", "cat": "general", "c": "LB", "nile": "12360 V 27500", "arab": None},
    {"id": 108, "name_ar": "التلفزيون الأردني", "name_en": "Jordan TV", "src": "levant", "src_id": "jordan_tv", "cat": "general", "c": "JO", "nile": "11958 H 27500", "arab": "12054 V 27500"},

    # =========================================================================
    # 12. KIDS & ANIMATION (3 Channels)
    # =========================================================================
    {"id": 109, "name_ar": "سبيستون", "name_en": "Spacetoon", "src": "kids", "src_id": "spacetoon", "cat": "kids", "c": "AE", "nile": "11785 V 27500", "arab": "12341 H 27500"},
    {"id": 110, "name_ar": "كرتون نتورك", "name_en": "Cartoon Network Arabic", "src": "kids", "src_id": "cn_arabic", "cat": "kids", "c": "AE", "nile": "11277 V 27500", "arab": "11747 H 27500"},
    {"id": 111, "name_ar": "قناة ماجد", "name_en": "Majid Kids", "src": "kids", "src_id": "majid", "cat": "kids", "c": "AE", "nile": "11411 H 30000", "arab": "11804 H 27500"},

    # =========================================================================
    # 13. NEWS & ZEE (4 Channels)
    # =========================================================================
    {"id": 112, "name_ar": "قناة العربية", "name_en": "Al Arabiya", "src": "news", "src_id": "alarabiya", "cat": "news", "c": "SA", "nile": "11747 V 27500", "arab": "11938 V 27500"},
    {"id": 113, "name_ar": "سكاي نيوز عربية", "name_en": "Sky News Arabia", "src": "news", "src_id": "skynews_ar", "cat": "news", "c": "AE", "nile": "11977 V 27500", "arab": "11996 H 27500"},
    {"id": 114, "name_ar": "زي ألوان", "name_en": "Zee Alwan", "src": "zee", "src_id": "zee_alwan", "cat": "drama", "c": "AE", "nile": "11277 V 27500", "arab": None},
    {"id": 115, "name_ar": "زي أفلام", "name_en": "Zee Aflam", "src": "zee", "src_id": "zee_aflam", "cat": "movies", "c": "AE", "nile": "11277 V 27500", "arab": None},

    # =========================================================================
    # 14. ADDITIONAL ELCINEMA CHANNELS (34 Channels)
    # =========================================================================
    {"id": 116, "name_ar": "إم بي سي 3", "name_en": "MBC 3", "src": "elcinema", "src_id": "mbc3", "cat": "kids", "c": "SA", "nile": "11470 V 27500", "arab": "11270 V 27500"},
    {"id": 117, "name_ar": "إم بي سي 5", "name_en": "MBC 5", "src": "elcinema", "src_id": "mbc5", "cat": "general", "c": "MA", "nile": "11470 V 27500", "arab": "11270 V 27500"},
    {"id": 118, "name_ar": "قناة ستار موفيز", "name_en": "Star Movies", "src": "elcinema", "src_id": "star_movies", "cat": "movies", "c": "AE", "nile": "11804 H 27500", "arab": None},
    {"id": 119, "name_ar": "قناة ستار أكشن", "name_en": "Star Action", "src": "elcinema", "src_id": "star_action", "cat": "action", "c": "AE", "nile": "11804 H 27500", "arab": None},
    {"id": 120, "name_ar": "قناة ستار ورلد", "name_en": "Star World", "src": "elcinema", "src_id": "star_world", "cat": "series", "c": "AE", "nile": "11804 H 27500", "arab": None},
    {"id": 121, "name_ar": "ميكس وان", "name_en": "Mix One", "src": "elcinema", "src_id": "mix_one", "cat": "movies", "c": "EG", "nile": "11843 H 27500", "arab": None},
    {"id": 122, "name_ar": "ميكس بالعربي", "name_en": "Mix BelArabi", "src": "elcinema", "src_id": "mix_belarabi", "cat": "drama", "c": "EG", "nile": "11843 H 27500", "arab": None},
    {"id": 123, "name_ar": "بي إن موفيز بريمير", "name_en": "beIN Movies Premiere", "src": "elcinema", "src_id": "bein_movies_premier", "cat": "movies", "c": "QA", "nile": "11013 H 27500", "arab": "11547 V 27500"},
    {"id": 124, "name_ar": "بي إن موفيز أكشن", "name_en": "beIN Movies Action", "src": "elcinema", "src_id": "bein_movies_action", "cat": "action", "c": "QA", "nile": "11013 H 27500", "arab": "11547 V 27500"},
    {"id": 125, "name_ar": "بي إن موفيز دراما", "name_en": "beIN Movies Drama", "src": "elcinema", "src_id": "bein_movies_drama", "cat": "drama", "c": "QA", "nile": "11013 H 27500", "arab": "11547 V 27500"},
    {"id": 126, "name_ar": "بي إن موفيز فاميلي", "name_en": "beIN Movies Family", "src": "elcinema", "src_id": "bein_movies_family", "cat": "movies", "c": "QA", "nile": "11013 H 27500", "arab": "11547 V 27500"},
    {"id": 127, "name_ar": "بي إن سيريس", "name_en": "beIN Series", "src": "elcinema", "src_id": "bein_series", "cat": "series", "c": "QA", "nile": "11013 H 27500", "arab": "11547 V 27500"},
    {"id": 128, "name_ar": "بي إن دراما", "name_en": "beIN Drama", "src": "elcinema", "src_id": "bein_drama", "cat": "drama", "c": "QA", "nile": "11013 H 27500", "arab": "11547 V 27500"},
    {"id": 129, "name_ar": "أو إس إن شوكيس", "name_en": "OSN Showcase", "src": "elcinema", "src_id": "osn_showcase", "cat": "entertainment", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 130, "name_ar": "أو إس إن كيدز", "name_en": "OSN Kids", "src": "elcinema", "src_id": "osn_kids", "cat": "kids", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 131, "name_ar": "أو إس إن كوميدي", "name_en": "OSN Comedy", "src": "elcinema", "src_id": "osn_comedy", "cat": "comedy", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 132, "name_ar": "أو إس إن كرايم", "name_en": "OSN Crime", "src": "elcinema", "src_id": "osn_crime", "cat": "action", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 133, "name_ar": "أو إس إن فاميلي", "name_en": "OSN Family", "src": "elcinema", "src_id": "osn_family", "cat": "variety", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 134, "name_ar": "أو إس إن وان", "name_en": "OSN One", "src": "elcinema", "src_id": "osn_one", "cat": "entertainment", "c": "AE", "nile": "11996 H 30000", "arab": "12073 H 30000"},
    {"id": 135, "name_ar": "قناة رؤيا", "name_en": "Roya TV", "src": "elcinema", "src_id": "roya_tv", "cat": "general", "c": "JO", "nile": "12398 V 27500", "arab": None},
    {"id": 136, "name_ar": "قناة الشرقية", "name_en": "Al Sharqiya", "src": "elcinema", "src_id": "alsharqiya", "cat": "general", "c": "IQ", "nile": "11785 V 27500", "arab": None},
    {"id": 137, "name_ar": "قناة السومرية", "name_en": "Al Sumaria", "src": "elcinema", "src_id": "alsumaria", "cat": "general", "c": "IQ", "nile": "12130 V 27500", "arab": None},
    {"id": 138, "name_ar": "قناة دجلة", "name_en": "Dijlah TV", "src": "elcinema", "src_id": "dijlah", "cat": "general", "c": "IQ", "nile": "12034 H 27500", "arab": None},
    {"id": 139, "name_ar": "قناة الرشيد", "name_en": "Al Rasheed", "src": "elcinema", "src_id": "alrasheed", "cat": "general", "c": "IQ", "nile": "12360 V 27500", "arab": None},
    {"id": 140, "name_ar": "قناة السعيدة", "name_en": "Al Saeeda", "src": "elcinema", "src_id": "alsaeeda", "cat": "general", "c": "YE", "nile": "11900 V 27500", "arab": None},
    {"id": 141, "name_ar": "تلفزيون حضرموت", "name_en": "Hadramout TV", "src": "elcinema", "src_id": "hadramout_tv", "cat": "general", "c": "YE", "nile": "12398 V 27500", "arab": None},
    {"id": 142, "name_ar": "الشروق الجزائرية", "name_en": "Echorouk TV", "src": "elcinema", "src_id": "echorouk_tv", "cat": "general", "c": "DZ", "nile": "10922 V 27500", "arab": None},
    {"id": 143, "name_ar": "قناة نسمة", "name_en": "Nessma TV", "src": "elcinema", "src_id": "nessma_tv", "cat": "general", "c": "TN", "nile": "11657 V 27500", "arab": None},
    {"id": 144, "name_ar": "الأولى المغربية", "name_en": "Al Aoula Morocco", "src": "elcinema", "src_id": "al_aoula_morocco", "cat": "general", "c": "MA", "nile": "11476 V 27500", "arab": "12683 V 27500"},
    {"id": 145, "name_ar": "قناة الظفرة", "name_en": "Al Dhafra", "src": "elcinema", "src_id": "aldhafra", "cat": "general", "c": "AE", "nile": "12322 V 27500", "arab": None},
    {"id": 146, "name_ar": "تلفزيون الفجيرة", "name_en": "Fujairah TV", "src": "elcinema", "src_id": "fujairah_tv", "cat": "general", "c": "AE", "nile": "12322 V 27500", "arab": None},
    {"id": 147, "name_ar": "التلفزيون العربي 2", "name_en": "Al Araby 2", "src": "elcinema", "src_id": "alaraby2", "cat": "variety", "c": "QA", "nile": "11258 H 27500", "arab": None},
    {"id": 148, "name_ar": "تلفزيون عمان", "name_en": "Oman TV", "src": "elcinema", "src_id": "oman_tv", "cat": "general", "c": "OM", "nile": "12111 H 27500", "arab": "12456 H 27500"},
    {"id": 149, "name_ar": "آي فيلم بالعربية", "name_en": "iFilm Arabic", "src": "elcinema", "src_id": "ifilm_ar", "cat": "movies", "c": "IR", "nile": "11641 H 27500", "arab": None},
]


def build_catalog():
    catalog = []
    for item in CHANNELS_DATA_FULL:
        freqs = []
        if item.get("nile"):
            parts = item["nile"].split()
            freqs.append({
                "satellite": "Nilesat 7.0°W",
                "frequency": parts[0],
                "polarization": parts[1] if len(parts) > 1 else "V",
                "symbol_rate": parts[2] if len(parts) > 2 else "27500",
                "fec": "5/6",
                "quality": "HD"
            })
        if item.get("arab"):
            parts = item["arab"].split()
            freqs.append({
                "satellite": "Arabsat Badr 26.0°E",
                "frequency": parts[0],
                "polarization": parts[1] if len(parts) > 1 else "V",
                "symbol_rate": parts[2] if len(parts) > 2 else "27500",
                "fec": "3/4",
                "quality": "HD"
            })
            
        badge_b64 = get_channel_badge_svg(item["src_id"], item["name_ar"])
        
        catalog.append({
            "id": item["id"],
            "name": item["name_en"],
            "name_ar": item["name_ar"],
            "name_en": item["name_en"],
            "logo_url": badge_b64,
            "source": item["src"],
            "source_channel_id": item["src_id"],
            "country": item["c"],
            "language": "ar",
            "category": item["cat"],
            "display_order": item["id"],
            "frequencies": freqs
        })

    code = f"""# =============================================================================
# TV Guide - Comprehensive Channels & Satellite Frequencies Catalog (115 Channels)
# =============================================================================

ALL_CHANNELS_CATALOG = {repr(catalog)}
"""
    Path("collectors/channels_catalog.py").write_text(code, encoding="utf-8")
    print(f"Mega catalog built successfully with {len(catalog)} channels (All Egyptian Channels included)!")


if __name__ == "__main__":
    build_catalog()
