package com.tvguide.app.data.classifier

import com.tvguide.app.util.ArabicSearchHelper
import java.security.MessageDigest

object CanonicalContentType {
    const val MOVIE = "movie"
    const val SERIES = "series"
    const val CARTOON = "cartoon"
    const val OTHER = "other"

    fun getPriority(type: String?): Int {
        val t = (type ?: "").lowercase().trim()
        return when {
            t.contains("movie") || t.contains("film") || t.contains("cinema") -> 1
            t.contains("series") || t.contains("drama") || t.contains("مسلسل") || t.contains("دراما") -> 2
            t.contains("cartoon") || t.contains("animation") || t.contains("anime") || t.contains("kids") || t.contains("كرتون") || t.contains("أطفال") -> 3
            else -> 4
        }
    }
}

object ClassificationSource {
    const val SOURCE_METADATA = "SOURCE_METADATA"
    const val CHANNEL_PROFILE = "CHANNEL_PROFILE"
    const val PROGRAM_METADATA = "PROGRAM_METADATA"
    const val TEXT_RULES = "TEXT_RULES"
    const val HISTORICAL = "HISTORICAL"
    const val DEFAULT_FALLBACK = "DEFAULT_FALLBACK"
}

data class ClassificationResult(
    val contentType: String,
    val confidence: Float,
    val source: String,
    val stableProgramId: String
) {
    val priority: Int
        get() = CanonicalContentType.getPriority(contentType)
}

data class ChannelProfile(
    val channelId: Long,
    val channelName: String,
    val primaryContentType: String,
    val confidence: Float,
    val source: String
)

object ChannelProfiler {
    private val MOVIE_KEYWORDS = listOf("cinema", "سينما", "movies", "أفلام", "افلام", "film", "mbc 2", "mbc max", "mbc action", "fox movies", "top movies")
    private val SERIES_KEYWORDS = listOf("drama", "دراما", "series", "مسلسلات", "حكايات", "mbc drama", "dmc drama", "cbc drama", "on drama")
    private val CARTOON_KEYWORDS = listOf("spacetoon", "سبيستون", "cartoon", "كرتون", "أطفال", "اطفال", "kids", "cn", "mbc 3", "ماجد", "majid", "nickelodeon", "boomerang")
    private val OTHER_KEYWORDS = listOf("news", "أخبار", "اخبار", "sports", "رياضة", "رياضه", "on sport", "al jazeera", "alarabiya", "العربية", "الجزيرة", "music", "موسيقى", "قرآن", "quran")

    fun detectNameSpecialization(channelName: String, category: String? = null): Pair<String?, Float> {
        val combined = (ArabicSearchHelper.normalizeArabic(channelName) + " " + ArabicSearchHelper.normalizeArabic(category ?: "")).lowercase()

        for (kw in MOVIE_KEYWORDS) {
            if (combined.contains(kw)) return Pair(CanonicalContentType.MOVIE, 0.95f)
        }
        for (kw in CARTOON_KEYWORDS) {
            if (combined.contains(kw)) return Pair(CanonicalContentType.CARTOON, 0.96f)
        }
        for (kw in SERIES_KEYWORDS) {
            if (combined.contains(kw)) return Pair(CanonicalContentType.SERIES, 0.94f)
        }
        for (kw in OTHER_KEYWORDS) {
            if (combined.contains(kw)) return Pair(CanonicalContentType.OTHER, 0.95f)
        }
        return Pair(null, 0.0f)
    }

    fun buildProfile(channelId: Long, channelName: String, category: String? = null): ChannelProfile {
        val (spec, conf) = detectNameSpecialization(channelName, category)
        return if (spec != null) {
            ChannelProfile(channelId, channelName, spec, conf, "CHANNEL_METADATA")
        } else {
            ChannelProfile(channelId, channelName, CanonicalContentType.OTHER, 0.50f, "DEFAULT_FALLBACK")
        }
    }
}

class ContentClassifier(
    private val historicalCache: MutableMap<String, ClassificationResult> = mutableMapOf()
) {
    private val channelProfiles = mutableMapOf<Long, ChannelProfile>()

    fun registerChannelProfile(profile: ChannelProfile) {
        channelProfiles[profile.channelId] = profile
    }

    fun classify(
        title: String,
        titleEn: String? = null,
        sourceProgramType: String? = null,
        category: String? = null,
        genre: String? = null,
        overview: String? = null,
        channelId: Long? = null,
        channelName: String? = null,
        sourceProgramId: String? = null
    ): ClassificationResult {
        val stableId = generateStableProgramId(title, titleEn, sourceProgramId)

        // 0. Pre-pass: Contextual Negative Signals / Exclusion Guards
        val normTit = ArabicSearchHelper.normalizeArabic(title)
        val normEn = (titleEn ?: "").lowercase()
        val normOv = ArabicSearchHelper.normalizeArabic(overview ?: "")
        val combinedText = "$normTit $normEn $normOv"

        val newsKeywords = listOf("اخبار", "أخبار", "نشره", "نشرة", "موجز", "حدث اليوم", "العاشره مساء", "التاسعه", "news", "bulletin", "gma news", "sky news", "bbc news", "bloomberg")
        val sportsKeywords = listOf("مباراه", "مباراة", "الدوري", "كاس", "كأس", "كوره", "كورة", "استوديو تحليلي", "استوديو", "ملعب", "sports", "sport", "match", "league", "cup", "championship", "goal", "بطوله", "بطولة", "تنس الطاوله", "تنس الطاولة", "الرياضه", "الرياضة")
        val religiousKeywords = listOf("قران", "قرآن", "اذان", "أذان", "صلاه", "صلاة", "دعاء", "خطبه", "خطبة", "تلاوه", "تلاوة", "الجمعه", "الجمعة", "تفسير", "quran", "prayer", "اذكار", "أذكار")
        val musicKeywords = listOf("حفل ام كلثوم", "حفل غنائي", "مهرجان الغناء", "اغاني", "أغاني", "كليب", "سهرة غنائية", "concert", "music video")
        val talkKeywords = listOf("صباح الورد", "صباح الخير", "صباح البحرين", "هذا الصباح", "هاذا الصباح", "مساء dmc", "مساء الخير", "توك شو", "talk show", "لقاء خاص", "حديث الصباح")

        val isObviouslyNews = newsKeywords.any { normTit.contains(it) } || listOf("نشرة الاخبار", "موجز الاخبار", "اخبار الخامسه", "اخبار الحدث", "اخبار العالم").any { combinedText.contains(it) }
        val isObviouslySports = sportsKeywords.any { normTit.contains(it) } || combinedText.contains("استوديو تحليلي")
        val isObviouslyReligious = religiousKeywords.any { normTit.contains(it) } || combinedText.contains("تلاوة خاشعة")
        val isObviouslyMusic = musicKeywords.any { normTit.contains(it) }
        val isObviouslyTalk = talkKeywords.any { normTit.contains(it) } && !normTit.startsWith("مسلسل") && normTit != "صباحو كدب"

        val seriesStrongMarkers = listOf("مسلسل", "حلقه", "حلقة", "الموسم", "الجزء الاول", "الجزء الثاني", "الجزء الثالث", "الجزء الرابع", "ج1", "ج2", "ج3", "ج4", "ج5", "season", "episode")
        val isStrongSeries = seriesStrongMarkers.any { normTit.contains(it) } || listOf("series", "season", "episode").any { normEn.contains(it) } || normTit.contains("رافت الهجان")

        // Strong series title overrides kids profile or missing type
        if (isStrongSeries && !isObviouslyNews) {
            val res = ClassificationResult(CanonicalContentType.SERIES, 0.98f, ClassificationSource.TEXT_RULES, stableId)
            historicalCache[stableId] = res
            return res
        }

        // Obviously News, Sports, Religious, Music or Talk show can NEVER be a MOVIE
        if (isObviouslyNews || isObviouslySports || isObviouslyReligious || isObviouslyMusic || isObviouslyTalk) {
            val res = ClassificationResult(CanonicalContentType.OTHER, 0.96f, ClassificationSource.TEXT_RULES, stableId)
            historicalCache[stableId] = res
            return res
        }

        // 1. Evidence Layer A: Explicit source metadata
        val srcPt = (sourceProgramType ?: "").trim().lowercase()
        val srcCat = (category ?: "").trim().lowercase()
        val srcGenre = (genre ?: "").trim().lowercase()
        val combinedSrc = "$srcPt $srcCat $srcGenre"

        if (combinedSrc.contains("movie") || combinedSrc.contains("film") || combinedSrc.contains("cinema") || combinedSrc.contains("أفلام") || combinedSrc.contains("افلام")) {
            val res = ClassificationResult(CanonicalContentType.MOVIE, 0.97f, ClassificationSource.SOURCE_METADATA, stableId)
            historicalCache[stableId] = res
            return res
        }

        if (combinedSrc.contains("series") || combinedSrc.contains("drama") || combinedSrc.contains("مسلسل") || combinedSrc.contains("دراما") || combinedSrc.contains("episode")) {
            val res = ClassificationResult(CanonicalContentType.SERIES, 0.97f, ClassificationSource.SOURCE_METADATA, stableId)
            historicalCache[stableId] = res
            return res
        }

        if (combinedSrc.contains("cartoon") || combinedSrc.contains("animation") || combinedSrc.contains("anime") || combinedSrc.contains("kids") || combinedSrc.contains("children") || combinedSrc.contains("كرتون") || combinedSrc.contains("أطفال") || combinedSrc.contains("رسوم متحركة")) {
            val res = ClassificationResult(CanonicalContentType.CARTOON, 0.97f, ClassificationSource.SOURCE_METADATA, stableId)
            historicalCache[stableId] = res
            return res
        }

        // 2. Evidence Layer B: Explicit Program Title / Text Rules
        if (normTit.startsWith("فيلم") || normTit.startsWith("فلم") || normEn.contains("movie")) {
            val res = ClassificationResult(CanonicalContentType.MOVIE, 0.96f, ClassificationSource.TEXT_RULES, stableId)
            historicalCache[stableId] = res
            return res
        }

        if (normTit.startsWith("مسلسل") || normTit.contains("حلقة") || normTit.contains("الموسم") || normEn.contains("series") || normEn.contains("season") || normEn.contains("episode")) {
            val res = ClassificationResult(CanonicalContentType.SERIES, 0.96f, ClassificationSource.TEXT_RULES, stableId)
            historicalCache[stableId] = res
            return res
        }

        if (normTit.contains("كرتون") || normTit.contains("رسوم متحركة") || normTit.contains("انمي") || normTit.contains("ابطال") || normTit.contains("مغامرات كرتون")) {
            val res = ClassificationResult(CanonicalContentType.CARTOON, 0.95f, ClassificationSource.TEXT_RULES, stableId)
            historicalCache[stableId] = res
            return res
        }

        // 3. Evidence Layer C: Program Overview Text
        if (normOv.contains("تدور احداث الفيلم") || normOv.contains("تدور قصه الفيلم") || (!normOv.contains("فيلم وثائقي") && normOv.contains("الفيلم"))) {
            val res = ClassificationResult(CanonicalContentType.MOVIE, 0.91f, ClassificationSource.PROGRAM_METADATA, stableId)
            historicalCache[stableId] = res
            return res
        }

        if (normOv.contains("تدور احداث المسلسل") || normOv.contains("تدور قصه المسلسل") || normOv.contains("المسلسل")) {
            val res = ClassificationResult(CanonicalContentType.SERIES, 0.91f, ClassificationSource.PROGRAM_METADATA, stableId)
            historicalCache[stableId] = res
            return res
        }

        // 4. Evidence Layer D: Channel Specialization / Profile
        var chProf = if (channelId != null) channelProfiles[channelId] else null
        if (chProf == null && channelName != null) {
            val (spec, conf) = ChannelProfiler.detectNameSpecialization(channelName)
            if (spec != null) {
                chProf = ChannelProfile(channelId ?: 0L, channelName, spec, conf, "CHANNEL_NAME_HEURISTIC")
            }
        }

        if (chProf != null && chProf.primaryContentType in listOf(CanonicalContentType.MOVIE, CanonicalContentType.SERIES, CanonicalContentType.CARTOON)) {
            if (chProf.confidence >= 0.80f) {
                val res = ClassificationResult(chProf.primaryContentType, chProf.confidence * 0.96f, ClassificationSource.CHANNEL_PROFILE, stableId)
                historicalCache[stableId] = res
                return res
            }
        }

        // 5. Evidence Layer E: Historical Learning of Stable Program ID
        val prev = historicalCache[stableId]
        if (prev != null && prev.confidence >= 0.70f) {
            return ClassificationResult(prev.contentType, prev.confidence * 0.95f, ClassificationSource.HISTORICAL, stableId)
        }

        // 6. Evidence Layer F: Default Fallback -> OTHER
        return ClassificationResult(CanonicalContentType.OTHER, 0.50f, ClassificationSource.DEFAULT_FALLBACK, stableId)
    }

    companion object {
        val defaultInstance = ContentClassifier()

        fun classify(
            title: String,
            titleEn: String? = null,
            sourceProgramType: String? = null,
            category: String? = null,
            genre: String? = null,
            overview: String? = null,
            channelId: Long? = null,
            channelName: String? = null,
            sourceProgramId: String? = null
        ): ClassificationResult {
            return defaultInstance.classify(
                title = title,
                titleEn = titleEn,
                sourceProgramType = sourceProgramType,
                category = category,
                genre = genre,
                overview = overview,
                channelId = channelId,
                channelName = channelName,
                sourceProgramId = sourceProgramId
            )
        }

        fun generateStableProgramId(title: String, titleEn: String? = null, sourceId: String? = null): String {
            if (!sourceId.isNullOrBlank()) {
                val cleanSid = sourceId.trim()
                if (cleanSid.length > 4 || !cleanSid.all { it.isDigit() }) {
                    return "prog_$cleanSid"
                }
            }

            val normAr = ArabicSearchHelper.normalizeArabic(title)
            val root = normAr.replace(Regex("^(فيلم|فلم|مسلسل|برنامج|سلسله)\\s+"), "").trim()
            val normEn = (titleEn ?: "").lowercase().replace(Regex("[^a-z0-9]"), "")
            val seed = "$root|$normEn".trim('|')

            return try {
                val md = MessageDigest.getInstance("SHA-256")
                val hashBytes = md.digest(seed.toByteArray(Charsets.UTF_8))
                val hex = hashBytes.joinToString("") { "%02x".format(it) }
                "prog_${hex.substring(0, 12)}"
            } catch (e: Exception) {
                "prog_${seed.hashCode()}"
            }
        }
    }
}

