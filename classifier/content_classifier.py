"""
TV Guide - Centralized Content Classifier & Channel Profiler
Single source of truth for canonical program classification, channel specialization profiling,
and global visual content priority across the entire system.
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple


class CanonicalContentType:
    MOVIE = "movie"
    SERIES = "series"
    CARTOON = "cartoon"
    OTHER = "other"


# Global Visual Content Priority (1: MOVIE, 2: SERIES, 3: CARTOON, 4: OTHER)
CONTENT_PRIORITY = {
    CanonicalContentType.MOVIE: 1,
    CanonicalContentType.SERIES: 2,
    CanonicalContentType.CARTOON: 3,
    CanonicalContentType.OTHER: 4,
}


class ClassificationSource:
    SOURCE_METADATA = "SOURCE_METADATA"
    CHANNEL_PROFILE = "CHANNEL_PROFILE"
    PROGRAM_METADATA = "PROGRAM_METADATA"
    TEXT_RULES = "TEXT_RULES"
    HISTORICAL = "HISTORICAL"
    DEFAULT_FALLBACK = "DEFAULT_FALLBACK"


@dataclass
class ClassificationResult:
    content_type: str
    confidence: float
    source: str
    stable_program_id: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contentType": self.content_type,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "priority": CONTENT_PRIORITY.get(self.content_type, 4),
            "programId": self.stable_program_id
        }


@dataclass
class ChannelProfile:
    channel_id: int
    channel_name: str
    primary_content_type: str
    confidence: float
    source: str
    stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "channelId": self.channel_id,
            "channelName": self.channel_name,
            "primaryContentType": self.primary_content_type,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "stats": self.stats
        }


def normalize_text_for_matching(text: Optional[str]) -> str:
    if not text:
        return ""
    t = text.strip().lower()
    # Normalize Arabic letters
    t = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", t)  # Tashkeel & Tatweel
    t = re.sub(r"[أإآٱ]", "ا", t)
    t = re.sub(r"ة", "ه", t)
    t = re.sub(r"[ىئ]", "ي", t)
    t = re.sub(r"ؤ", "و", t)
    return t


def generate_stable_program_id(title: str, title_en: Optional[str] = None, source_id: Optional[str] = None) -> str:
    """Generates a stable, deterministic program identity across runs."""
    if source_id and str(source_id).strip():
        clean_sid = str(source_id).strip()
        if not clean_sid.isdigit() or len(clean_sid) > 4:
            return f"prog_{clean_sid}"

    norm_ar = normalize_text_for_matching(title)
    # Remove common prefixes like "فيلم", "مسلسل", "برنامج" for root matching
    root = re.sub(r"^(فيلم|فلم|مسلسل|برنامج|سلسله)\s+", "", norm_ar).strip()
    norm_en = (title_en or "").strip().lower()
    norm_en = re.sub(r"[^a-z0-9]", "", norm_en)

    seed = f"{root}|{norm_en}".strip("|")
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]
    return f"prog_{digest}"


class ChannelProfiler:
    """Analyzes channel metadata, names, and historical broadcast schedules to determine channel specialization."""

    MOVIE_NAME_KEYWORDS = ["cinema", "سينما", "movies", "أفلام", "افلام", "film", "mbc 2", "mbc max", "mbc action", "fox movies", "top movies"]
    SERIES_NAME_KEYWORDS = ["drama", "دراما", "series", "مسلسلات", "حكايات", "mbc drama", "dmc drama", "cbc drama", "on drama"]
    CARTOON_NAME_KEYWORDS = ["spacetoon", "سبيستون", "cartoon", "كرتون", "أطفال", "اطفال", "kids", "cn", "mbc 3", "ماجد", "majid", "nickelodeon", "boomerang"]
    OTHER_NAME_KEYWORDS = ["news", "أخبار", "اخبار", "sports", "رياضة", "رياضه", "on sport", "al jazeera", "alarabiya", "العربية", "الجزيرة", "music", "موسيقى", "قرآن", "quran"]

    @classmethod
    def detect_name_specialization(cls, channel_name: str, category: Optional[str] = None) -> Tuple[Optional[str], float]:
        name_norm = normalize_text_for_matching(channel_name)
        cat_norm = normalize_text_for_matching(category or "")
        combined = f"{name_norm} {cat_norm}"

        for kw in cls.MOVIE_NAME_KEYWORDS:
            if kw in combined:
                return (CanonicalContentType.MOVIE, 0.95)

        for kw in cls.CARTOON_NAME_KEYWORDS:
            if kw in combined:
                return (CanonicalContentType.CARTOON, 0.96)

        for kw in cls.SERIES_NAME_KEYWORDS:
            if kw in combined:
                return (CanonicalContentType.SERIES, 0.94)

        for kw in cls.OTHER_NAME_KEYWORDS:
            if kw in combined:
                return (CanonicalContentType.OTHER, 0.95)

        return (None, 0.0)

    @classmethod
    def build_profile(
        cls,
        channel_id: int,
        channel_name: str,
        category: Optional[str] = None,
        schedules: Optional[List[Dict[str, Any]]] = None
    ) -> ChannelProfile:
        name_spec, name_conf = cls.detect_name_specialization(channel_name, category)

        if not schedules:
            if name_spec:
                return ChannelProfile(
                    channel_id=channel_id,
                    channel_name=channel_name,
                    primary_content_type=name_spec,
                    confidence=name_conf,
                    source="CHANNEL_METADATA",
                    stats={"total_samples": 0}
                )
            return ChannelProfile(
                channel_id=channel_id,
                channel_name=channel_name,
                primary_content_type=CanonicalContentType.OTHER,
                confidence=0.50,
                source="DEFAULT_FALLBACK",
                stats={"total_samples": 0}
            )

        # Analyze historical schedule composition
        counts = {
            CanonicalContentType.MOVIE: 0,
            CanonicalContentType.SERIES: 0,
            CanonicalContentType.CARTOON: 0,
            CanonicalContentType.OTHER: 0
        }
        total = 0

        for s in schedules:
            pt = (s.get("programType") or "").lower()
            tit = s.get("title", "")
            t_norm = normalize_text_for_matching(tit)

            # Quick heuristic categorization for schedule sample
            if "movie" in pt or "film" in pt or "cinema" in pt or t_norm.startswith("فيلم"):
                counts[CanonicalContentType.MOVIE] += 1
            elif "series" in pt or "drama" in pt or "مسلسل" in pt or t_norm.startswith("مسلسل"):
                counts[CanonicalContentType.SERIES] += 1
            elif "cartoon" in pt or "animation" in pt or "kids" in pt or "anime" in pt or "كرتون" in pt:
                counts[CanonicalContentType.CARTOON] += 1
            else:
                counts[CanonicalContentType.OTHER] += 1
            total += 1

        stats = {
            "total_samples": total,
            "movie_ratio": round(counts[CanonicalContentType.MOVIE] / total, 3) if total else 0.0,
            "series_ratio": round(counts[CanonicalContentType.SERIES] / total, 3) if total else 0.0,
            "cartoon_ratio": round(counts[CanonicalContentType.CARTOON] / total, 3) if total else 0.0,
            "other_ratio": round(counts[CanonicalContentType.OTHER] / total, 3) if total else 0.0,
        }

        # Find dominant type from schedule
        dominant_type = max(counts.items(), key=lambda x: x[1])
        dom_ratio = (dominant_type[1] / total) if total > 0 else 0.0

        if dom_ratio >= 0.70:
            hist_spec = dominant_type[0]
            hist_conf = min(0.98, 0.85 + (dom_ratio * 0.13))
            # If name and history agree -> extremely high confidence 0.98
            if name_spec == hist_spec:
                return ChannelProfile(channel_id, channel_name, hist_spec, 0.98, "CHANNEL_PROFILE_CONSENSUS", stats)
            # History overrides if strong enough
            return ChannelProfile(channel_id, channel_name, hist_spec, hist_conf, "SCHEDULE_HISTORY", stats)

        if name_spec:
            return ChannelProfile(channel_id, channel_name, name_spec, name_conf, "CHANNEL_METADATA", stats)

        return ChannelProfile(channel_id, channel_name, CanonicalContentType.OTHER, 0.50, "DEFAULT_FALLBACK", stats)


class ContentClassifier:
    """Centralized, evidence-based program classifier combining:
    1. Explicit source metadata
    2. Channel specialization / profile
    3. Program metadata
    4. Text rules
    5. Historical classifications
    """

    def __init__(self, historical_cache: Optional[Dict[str, ClassificationResult]] = None):
        self.history: Dict[str, ClassificationResult] = historical_cache or {}
        self.channel_profiles: Dict[int, ChannelProfile] = {}

    def register_channel_profile(self, profile: ChannelProfile):
        self.channel_profiles[profile.channel_id] = profile

    def classify(
        self,
        title: str,
        title_en: Optional[str] = None,
        source_program_type: Optional[str] = None,
        category: Optional[str] = None,
        genre: Optional[str] = None,
        overview: Optional[str] = None,
        channel_id: Optional[int] = None,
        channel_name: Optional[str] = None,
        source_program_id: Optional[str] = None
    ) -> ClassificationResult:
        stable_id = generate_stable_program_id(title, title_en, source_program_id)

        # -----------------------------------------------------------------------------------------
        # Pre-pass: Contextual Negative Signals / Exclusion Guards
        # -----------------------------------------------------------------------------------------
        norm_tit = normalize_text_for_matching(title)
        norm_en = (title_en or "").lower()
        norm_ov = normalize_text_for_matching(overview or "")
        combined_text = f"{norm_tit} {norm_en} {norm_ov}"

        NEWS_KEYWORDS = ["اخبار", "أخبار", "نشره", "نشرة", "موجز", "حدث اليوم", "العاشره مساء", "التاسعه", "news", "bulletin", "gma news", "sky news", "bbc news", "bloomberg"]
        SPORTS_KEYWORDS = ["مباراه", "مباراة", "الدوري", "كاس", "كأس", "كوره", "كورة", "استوديو تحليلي", "استوديو", "ملعب", "sports", "sport", "match", "league", "cup", "championship", "goal", "بطوله", "بطولة", "تنس الطاوله", "تنس الطاولة", "الرياضه", "الرياضة"]
        RELIGIOUS_KEYWORDS = ["قران", "قرآن", "اذان", "أذان", "صلاه", "صلاة", "دعاء", "خطبه", "خطبة", "تلاوه", "تلاوة", "الجمعه", "الجمعة", "تفسير", "quran", "prayer", "اذكار", "أذكار"]
        MUSIC_VARIETY_KEYWORDS = ["حفل ام كلثوم", "حفل غنائي", "مهرجان الغناء", "اغاني", "أغاني", "كليب", "سهرة غنائية", "concert", "music video"]
        TALK_GENERAL_KEYWORDS = ["صباح الورد", "صباح الخير", "صباح البحرين", "هذا الصباح", "هاذا الصباح", "مساء dmc", "مساء الخير", "توك شو", "talk show", "لقاء خاص", "حديث الصباح"]

        GENERIC_CHANNEL_PLACEHOLDERS = ["الراي", "العربية", "الحدث", "الأخبار", "الاخبار", "المستقبل", "الشروق", "النهار", "الوطن", "تلفزيوني", "منوعات", "اف دي ال", "myx", "ktv 1", "ktv", "bloomberg originals", "وثائقي", "تلفزيون السعودية", "تلفزيون البحرين", "بي بي سي نيوز", "bbc news"]
        is_channel_placeholder = any(norm_tit == normalize_text_for_matching(p) for p in GENERIC_CHANNEL_PLACEHOLDERS)

        is_obviously_news = is_channel_placeholder or any(k in norm_tit for k in NEWS_KEYWORDS) or any(k in combined_text for k in ["نشرة الاخبار", "موجز الاخبار", "اخبار الخامسه", "اخبار السادسه", "اخبار التاسعه", "اخبار العاشره", "اخبار الحدث", "اخبار العالم"])
        is_obviously_sports = any(k in norm_tit for k in SPORTS_KEYWORDS) or "استوديو تحليلي" in combined_text
        is_obviously_religious = any(k in norm_tit for k in RELIGIOUS_KEYWORDS) or "تلاوة خاشعة" in combined_text
        is_obviously_music_variety = any(k in norm_tit for k in MUSIC_VARIETY_KEYWORDS)
        is_obviously_talk = any(k in norm_tit for k in TALK_GENERAL_KEYWORDS) and not norm_tit.startswith("مسلسل") and norm_tit != "صباحو كدب"

        # -----------------------------------------------------------------------------------------
        # Evidence Layer A: Explicit source metadata
        # -----------------------------------------------------------------------------------------
        src_pt = (source_program_type or "").strip().lower()
        src_cat = (category or "").strip().lower()
        src_genre = (genre or "").strip().lower()
        combined_src = f"{src_pt} {src_cat} {src_genre}"

        if any(k in combined_src for k in ["movie", "film", "cinema", "أفلام", "افلام"]) and not (is_obviously_news or is_obviously_sports or is_obviously_religious):
            res = ClassificationResult(CanonicalContentType.MOVIE, 0.97, ClassificationSource.SOURCE_METADATA, stable_id)
            self.history[stable_id] = res
            return res

        if any(k in combined_src for k in ["series", "drama", "مسلسل", "دراما", "episode"]) and not is_obviously_news:
            res = ClassificationResult(CanonicalContentType.SERIES, 0.97, ClassificationSource.SOURCE_METADATA, stable_id)
            self.history[stable_id] = res
            return res

        if any(k in combined_src for k in ["cartoon", "animation", "anime", "kids", "children", "كرتون", "أطفال", "رسوم متحركة"]):
            res = ClassificationResult(CanonicalContentType.CARTOON, 0.97, ClassificationSource.SOURCE_METADATA, stable_id)
            self.history[stable_id] = res
            return res

        # Explicit series markers that should NEVER be confused with cartoon or movie
        SERIES_STRONG_MARKERS = ["مسلسل", "حلقه", "حلقة", "الموسم", "الجزء الاول", "الجزء الثاني", "الجزء الثالث", "الجزء الرابع", "ج1", "ج2", "ج3", "ج4", "ج5", "season", "episode"]
        is_strong_series = any(k in norm_tit for k in SERIES_STRONG_MARKERS) or any(k in norm_en for k in ["series", "season", "episode"]) or "رافت الهجان" in norm_tit

        # If it's a clear Series by title (like رأفت الهجان ج1), it is SERIES regardless of channel kids profile or missing type
        if is_strong_series and not is_obviously_news:
            res = ClassificationResult(CanonicalContentType.SERIES, 0.98, ClassificationSource.TEXT_RULES, stable_id)
            self.history[stable_id] = res
            return res

        # If it's obviously News, Sports, Religious, Music, or Talk show, it can NEVER be a MOVIE
        if is_obviously_news or is_obviously_sports or is_obviously_religious or is_obviously_music_variety or is_obviously_talk:
            res = ClassificationResult(CanonicalContentType.OTHER, 0.96, ClassificationSource.TEXT_RULES, stable_id)
            self.history[stable_id] = res
            return res

        # -----------------------------------------------------------------------------------------
        # Evidence Layer B: Explicit Program Title / Text Rules
        # -----------------------------------------------------------------------------------------

        # Direct Arabic title prefixes
        if norm_tit.startswith("فيلم") or norm_tit.startswith("فلم") or "movie" in norm_en:
            res = ClassificationResult(CanonicalContentType.MOVIE, 0.96, ClassificationSource.TEXT_RULES, stable_id)
            self.history[stable_id] = res
            return res

        if (
            norm_tit.startswith("مسلسل") or "حلقة" in norm_tit or "الموسم" in norm_tit or
            "series" in norm_en or "season" in norm_en or "episode" in norm_en
        ):
            res = ClassificationResult(CanonicalContentType.SERIES, 0.96, ClassificationSource.TEXT_RULES, stable_id)
            self.history[stable_id] = res
            return res

        if any(k in norm_tit for k in ["كرتون", "رسوم متحركه", "انمي", "ابطال", "مغامرات كرتون"]):
            res = ClassificationResult(CanonicalContentType.CARTOON, 0.95, ClassificationSource.TEXT_RULES, stable_id)
            self.history[stable_id] = res
            return res

        # -----------------------------------------------------------------------------------------
        # Evidence Layer C: Program Overview Text
        # -----------------------------------------------------------------------------------------
        norm_ov = normalize_text_for_matching(overview or "")
        if "تدور احداث الفيلم" in norm_ov or "تدور قصه الفيلم" in norm_ov or "فيلم وثائقي" not in norm_ov and "الفيلم" in norm_ov:
            res = ClassificationResult(CanonicalContentType.MOVIE, 0.91, ClassificationSource.PROGRAM_METADATA, stable_id)
            self.history[stable_id] = res
            return res

        if "تدور احداث المسلسل" in norm_ov or "تدور قصه المسلسل" in norm_ov or "المسلسل" in norm_ov:
            res = ClassificationResult(CanonicalContentType.SERIES, 0.91, ClassificationSource.PROGRAM_METADATA, stable_id)
            self.history[stable_id] = res
            return res

        # -----------------------------------------------------------------------------------------
        # Evidence Layer D: Channel Specialization / Profile
        # -------------------------------------------------------------------------
        ch_prof = self.channel_profiles.get(channel_id) if channel_id is not None else None
        if not ch_prof and channel_name:
            spec, conf = ChannelProfiler.detect_name_specialization(channel_name)
            if spec:
                ch_prof = ChannelProfile(channel_id or 0, channel_name, spec, conf, "CHANNEL_NAME_HEURISTIC")

        if ch_prof and ch_prof.primary_content_type in [CanonicalContentType.MOVIE, CanonicalContentType.SERIES, CanonicalContentType.CARTOON]:
            if ch_prof.confidence >= 0.80:
                res = ClassificationResult(ch_prof.primary_content_type, ch_prof.confidence * 0.96, ClassificationSource.CHANNEL_PROFILE, stable_id)
                self.history[stable_id] = res
                return res

        # -----------------------------------------------------------------------------------------
        # Evidence Layer E: Historical Learning of Stable Program ID
        # -------------------------------------------------------------------------
        if stable_id in self.history:
            prev = self.history[stable_id]
            if prev.confidence >= 0.70:
                return ClassificationResult(prev.content_type, prev.confidence * 0.95, ClassificationSource.HISTORICAL, stable_id)

        # -----------------------------------------------------------------------------------------
        # Evidence Layer F: Default Fallback -> OTHER
        # -------------------------------------------------------------------------
        res = ClassificationResult(CanonicalContentType.OTHER, 0.50, ClassificationSource.DEFAULT_FALLBACK, stable_id)
        return res

