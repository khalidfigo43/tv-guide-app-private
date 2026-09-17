package com.tvguide.app.data.repository

import android.content.Context
import com.tvguide.app.data.classifier.CanonicalContentType
import com.tvguide.app.data.classifier.ContentClassifier
import com.tvguide.app.data.api.TvGuideApi
import com.tvguide.app.data.db.TvGuideDatabase
import com.tvguide.app.data.models.*
import com.tvguide.app.util.ArabicSearchHelper
import com.tvguide.app.util.TimezoneHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.*
import java.io.File
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Locale

@Serializable
data class RawScheduleItem(
    val channelId: Long? = null,
    val channelName: String? = null,
    val channelLogo: String? = null,
    val title: String? = null,
    val title_en: String? = null,
    val date: String? = null,
    val startTime: String? = null,
    val endTime: String? = null,
    val poster: String? = null,
    val overview: String? = null,
    val programType: String? = "movie",
    val rating: String? = "7.5",
    val cast: List<CastMember> = emptyList(),
    val is_paid: Boolean = false,
    val programId: String? = null
)

@Serializable
data class RawProgramItem(
    val programId: String? = null,
    val title: String? = null,
    val title_en: String? = null,
    val programType: String? = "movie",
    val poster: String? = null,
    val overview: String? = null,
    val rating: String? = "7.5",
    val cast: List<CastMember> = emptyList()
)

@Serializable
data class ScheduleKey(
    val channelId: Long = 0L,
    val date: String = "",
    val startTime: String = ""
)

@Serializable
data class DeltaPayload(
    val version: Int = 0,
    val previousVersion: Int = 0,
    val generatedAt: String = "",
    val added: List<RawScheduleItem> = emptyList(),
    val updated: List<RawScheduleItem> = emptyList(),
    val deleted: List<ScheduleKey> = emptyList()
)

@Serializable
data class RemoteMetadata(
    val version: Int = 0,
    val previousVersion: Int = 0,
    val generatedAt: String = "",
    val delta: RemoteDeltaInfo? = null
)

@Serializable
data class RemoteDeltaInfo(
    val availableFrom: Int = 0,
    val url: String = ""
)

data class IndexedChannel(
    val id: Long,
    val nameNorm: String,
    val nameEnNorm: String,
    val categoryNorm: String,
    val isPaid: Boolean,
    val channel: Channel
)

class TvGuideRepository(
    private val context: Context? = null,
    private val api: TvGuideApi? = null
) {
    private val json = Json { ignoreUnknownKeys = true; isLenient = true; coerceInputValues = true }
    val database: TvGuideDatabase? = context?.let { TvGuideDatabase(it) }

    private var cachedChannels: List<Channel> = emptyList()
    private var channelMap: Map<Long, Channel> = emptyMap()
    private var paidChannelIds: Set<Long> = emptySet()
    private var indexedChannels: List<IndexedChannel> = emptyList()

    private var isLoaded: Boolean = false

    var liveUpdateUrl: String = "https://raw.githubusercontent.com/khalidfigo43/tv-guide-releases/main/data/schedules.json"

    fun isPermanentlyDeletedChannel(id: Long, name: String?): Boolean {
        if (id in setOf(91L, 179L, 196L, 200L, 203L, 204L, 216L, 217L, 234L, 235L, 236L, 238L, 239L, 240L, 241L, 250L, 251L, 252L, 253L, 254L, 255L, 256L, 257L, 258L, 259L, 260L)) return true
        if (name.isNullOrBlank()) return false
        val n = name.lowercase().trim()
        return n.contains("kapatid") ||
               n.contains("rfm tv") ||
               n.contains("mcm top") ||
               n.contains("dzmm") ||
               n.contains("teleradyo") ||
               n.contains("mor global") ||
               n.contains("rt english") ||
               n.contains("rt arabic") ||
               n.contains("روسيا اليوم") ||
               n.contains("cinemo") ||
               n.contains("gma pinoy") ||
               n.contains("gma life") ||
               n.contains("padel") ||
               n.contains("stv1") ||
               n.contains("stv 1") ||
               n.contains("تلفزيون البحرين") ||
               n.contains("bahrain tv") ||
               n == "anc"
    }

    fun isIgnoredChannel(id: Long, name: String?): Boolean {
        return isEsportsChannelName(name) || isPermanentlyDeletedChannel(id, name)
    }

    fun isEsportsChannelName(name: String?): Boolean {
        if (name.isNullOrBlank()) return false
        val n = name.lowercase()
        return n.contains("esport") ||
               n.contains("e-sport") ||
               n.contains("eclutch") ||
               n.contains("gametoon") ||
               n.contains("ginx") ||
               n.contains("gaming") ||
               n.contains("العاب إلكترونية") ||
               n.contains("رياضات إلكترونية") ||
               n.contains("ألعاب إلكترونية")
    }

    fun getContentBrowseTier(type: String?, title: String?, titleEn: String?, channelName: String?): Int {
        val t = (type ?: "").lowercase().trim()
        val tit = (title ?: "").lowercase().trim()
        val ch = (channelName ?: "").lowercase().trim()
        val normTit = ArabicSearchHelper.normalizeArabic(tit)
        val normCh = ArabicSearchHelper.normalizeArabic(ch)

        // 1. Negative rules: talk shows, sports, news, religion, morning shows, etc. are ALWAYS Tier 4 (Other)
        val isNegative = normTit.contains("اخبار") || normTit.contains("أخبار") || normTit.contains("نشره") ||
                normTit.contains("نشرة") || normTit.contains("موجز") || normTit.contains("مباراه") || normTit.contains("مباراة") ||
                normTit.contains("الدوري") || normTit.contains("كاس") || normTit.contains("كأس") || normTit.contains("بطولة") ||
                normTit.contains("بطوله") || normTit.contains("رياضة") || normTit.contains("رياضه") || normTit.contains("قران") ||
                normTit.contains("قرآن") || normTit.contains("اذان") || normTit.contains("أذان") || normTit.contains("صلاه") ||
                normTit.contains("صلاة") || normTit.contains("صباح الخير") || normTit.contains("صباح الورد") || normTit.contains("صباحك") ||
                normTit.contains("احلي اكله") || normTit.contains("أحلى أكلة") || normTit.contains("مطبخ") || normTit.contains("الشيف") ||
                normTit.contains("90 دقيقة") || normTit.contains("90 دقيقه") || normTit.contains("الحكاية") || normTit.contains("الحكايه") ||
                normTit.contains("معكم منى الشاذلي") || normTit.contains("كل يوم") || normTit.contains("مساء dmc") ||
                normTit.contains("يحدث في مصر") || normTit.contains("علي مسئوليتي") || normTit.contains("على مسئوليتي") ||
                normTit.contains("كلمة اخيرة") || normTit.contains("حفل") || normTit.contains("طرب") || normTit.contains("استوديو") ||
                normTit.contains("برامج") || normTit.contains("بث ليلي")

        if (isNegative && !normTit.startsWith("مسلسل") && !normTit.contains("رافت الهجان") && !normTit.contains("فيلم")) {
            return 4 // OTHER
        }

        // 2. Channel Specialization Profile
        val isMovieChannel = normCh.contains("سينما") || normCh.contains("cinema") || normCh.contains("movies") ||
                normCh.contains("أفلام") || normCh.contains("افلام") || normCh.contains("mbc 2") || normCh.contains("mbc max") ||
                normCh.contains("mbc action") || normCh.contains("fox movies") || normCh.contains("top movies") ||
                normCh.contains("star action") || normCh.contains("دبي ون") || normCh.contains("dubai one") ||
                normCh.contains("سيما")

        val isSeriesChannel = normCh.contains("دراما") || normCh.contains("drama") || normCh.contains("حكايات") ||
                normCh.contains("زي الوان") || normCh.contains("زي ألوان") || normCh.contains("zee alwan")

        val isCartoonChannel = normCh.contains("سبيستون") || normCh.contains("spacetoon") || normCh.contains("كرتون") ||
                normCh.contains("cartoon") || normCh.contains("اطفال") || normCh.contains("أطفال") || normCh.contains("kids") ||
                normCh.contains("ماجد") || normCh.contains("majid") || normCh.contains("mbc 3") || normCh.contains("براعم") ||
                normCh.contains("cn")

        // 3. Explicit Title Indicators
        val isMovieTitle = normTit.startsWith("فيلم") || normTit.contains(" فيلم ") || normTit.contains("movie") || normTit.contains("film")
        val isSeriesTitle = normTit.startsWith("مسلسل") || normTit.contains(" مسلسل ") || normTit.contains("series") ||
                normTit.contains("ج1") || normTit.contains("ج2") || normTit.contains("ج3") || normTit.contains("ج4") ||
                normTit.contains("ج5") || normTit.contains("ج6") || normTit.contains("ج7") || normTit.contains("ج8") ||
                normTit.contains("ج9") || normTit.contains("ج10") || normTit.contains("الجزء") || normTit.contains("حلقة")
        val isCartoonTitle = normTit.startsWith("كارتون") || normTit.contains("كارتون") || normTit.contains("كرتون") ||
                normTit.contains("رسوم متحركة") || normTit.contains("انمي") || normTit.contains("أنيمي") || normTit.contains("animation")

        // 1. MOVIES (Arabic & Foreign)
        if (isMovieTitle || isMovieChannel || t == "movie" || t.contains("movie") || t == "film") {
            return 1
        }

        // 2. SERIES (Arabic & Foreign)
        if (isSeriesTitle || isSeriesChannel || t == "series" || t.contains("series") || t == "drama") {
            return 2
        }

        // 3. CARTOONS
        if (isCartoonTitle || isCartoonChannel || t == "cartoon" || t == "kids" || t.contains("animation")) {
            return 3
        }

        // 4. Classifier Fallback
        val classified = ContentClassifier.classify(
            title = title ?: "",
            titleEn = titleEn,
            sourceProgramType = type,
            channelName = channelName
        )
        return CanonicalContentType.getPriority(classified.contentType)
    }

    fun parseDateTimeToMillis(dateStr: String, timeStr: String, allowNextDay: Boolean = false): Long {
        return try {
            val dParts = dateStr.split("-").map { it.toInt() }
            val tParts = timeStr.split(":").map { it.toInt() }
            if (dParts.size == 3 && tParts.size >= 2) {
                val cal = Calendar.getInstance()
                cal.set(dParts[0], dParts[1] - 1, dParts[2], tParts[0], tParts[1], 0)
                cal.set(Calendar.MILLISECOND, 0)
                if (allowNextDay) {
                    cal.add(Calendar.DAY_OF_MONTH, 1)
                }
                cal.timeInMillis
            } else 0L
        } catch (e: Exception) {
            0L
        }
    }

    private fun ensureDataLoaded() {
        if (isLoaded || context == null) return
        try {
            var channelsLoaded: List<Channel>? = null
            val internalChannelsFile = File(context.filesDir, "channels.json")
            if (internalChannelsFile.exists() && internalChannelsFile.length() > 0) {
                try {
                    val text = internalChannelsFile.readText(Charsets.UTF_8)
                    channelsLoaded = json.decodeFromString<List<Channel>>(text)
                } catch (e: Exception) {
                    internalChannelsFile.delete()
                }
            }

            if (channelsLoaded.isNullOrEmpty()) {
                try {
                    val text = context.assets.open("channels.json").bufferedReader().use { it.readText() }
                    channelsLoaded = json.decodeFromString<List<Channel>>(text)
                } catch (e: Exception) {
                    android.util.Log.e("TvGuideRepository", "Failed loading channels from assets: ${e.message}", e)
                }
            }

            cachedChannels = (channelsLoaded ?: emptyList())
                .filter { !isIgnoredChannel(it.id, it.displayName) && !isIgnoredChannel(it.id, it.nameEn) && !isIgnoredChannel(it.id, it.nameAr) }
            channelMap = cachedChannels.associateBy { it.id }
            paidChannelIds = cachedChannels.filter { it.isPaidChannel }.map { it.id }.toSet()

            indexedChannels = cachedChannels.map { ch ->
                IndexedChannel(
                    id = ch.id,
                    nameNorm = ArabicSearchHelper.normalizeArabic(ch.displayName),
                    nameEnNorm = ArabicSearchHelper.normalizeArabic(ch.nameEn),
                    categoryNorm = ArabicSearchHelper.normalizeArabic(ch.category),
                    isPaid = ch.isPaidChannel,
                    channel = ch
                )
            }

            isLoaded = true
        } catch (e: Exception) {
            android.util.Log.e("TvGuideRepository", "ensureDataLoaded failed: ${e.message}", e)
        }
    }

    suspend fun getChannels(category: String? = null, includePaid: Boolean = false): Result<List<Channel>> = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        var filtered = cachedChannels
        if (!includePaid) {
            filtered = filtered.filter { !it.isPaidChannel && !paidChannelIds.contains(it.id) }
        }
        if (!category.isNullOrBlank() && category != "all") {
            val catLower = category.lowercase().trim()
            filtered = filtered.filter { (it.category ?: "").lowercase().trim() == catLower }
        }
        val db = database
        if (db != null) {
            val activeChannelIds = try {
                val set = mutableSetOf<Long>()
                db.readableDatabase.rawQuery("SELECT DISTINCT channel_id FROM schedules", null).use { cur ->
                    while (cur.moveToNext()) set.add(cur.getLong(0))
                }
                set
            } catch (e: Exception) {
                emptySet()
            }
            if (activeChannelIds.isNotEmpty()) {
                filtered = filtered.sortedByDescending { activeChannelIds.contains(it.id) }
            }
        }
        Result.success(filtered)
    }

    suspend fun getChannelById(id: Long): Channel? = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        channelMap[id]
    }

    suspend fun getNowAiring(includePaid: Boolean = false, timezoneOffset: Int = 0): Result<List<NowAiringItem>> = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        val db = database ?: return@withContext Result.success(emptyList())

        try {
            val cal = Calendar.getInstance()
            val nowMillis = cal.timeInMillis
            val sdfDate = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
            val todayDateStr = sdfDate.format(cal.time)
            val sdfTime = SimpleDateFormat("HH:mm", Locale.getDefault())
            val nowTimeStr = sdfTime.format(cal.time)

            cal.add(Calendar.DAY_OF_MONTH, -1)
            val yesterdayDateStr = sdfDate.format(cal.time)

            val rawRows = db.getLiveNowSchedules(todayDateStr, yesterdayDateStr, nowTimeStr)
            val groupedByChannel = rawRows.groupBy { it.channelId }
            val items = mutableListOf<NowAiringItem>()

            for ((chId, chRows) in groupedByChannel) {
                val ch = channelMap[chId] ?: continue
                if (isIgnoredChannel(chId, ch.displayName) || isIgnoredChannel(chId, ch.nameEn) || isIgnoredChannel(chId, ch.nameAr)) continue
                if (!includePaid && (paidChannelIds.contains(chId) || ch.isPaidChannel)) continue

                val current = chRows.firstOrNull() ?: continue
                if (isEsportsChannelName(current.title)) continue

                val title = current.title.trim()
                val st = current.startTime
                val et = current.endTime ?: "13:00"
                val logo = ch?.logoUrl
                val poster = current.poster
                val overview = current.overview
                val rating = current.rating ?: "7.5"
                val channelName = ch?.displayName ?: "قناة"

                val sMillis = parseDateTimeToMillis(current.date, st)
                val eMillis = parseDateTimeToMillis(current.date, et, allowNextDay = et < st)
                val totalDurationMin = ((eMillis - sMillis) / (60 * 1000)).toInt().coerceAtLeast(1)
                val elapsedMin = ((nowMillis - sMillis) / (60 * 1000)).toInt().coerceIn(0, totalDurationMin)
                val progress = ((elapsedMin * 100) / totalDurationMin).coerceIn(5, 95)
                val remaining = ((eMillis - nowMillis) / (60 * 1000)).toInt().coerceIn(1, 180)

                val targetContentId = if (current.showId > 0L) current.showId else (current.programId ?: title).hashCode().toLong()

                items.add(
                    NowAiringItem(
                        broadcastId = chId * 1000L + items.size,
                        channelId = chId,
                        channelName = channelName,
                        channelLogo = logo,
                        contentId = targetContentId,
                        title = title,
                        titleEn = current.titleEn,
                        contentType = current.programType,
                        releaseYear = 2024,
                        rating = rating,
                        posterPath = poster,
                        backdropPath = poster,
                        overview = overview,
                        startTime = TimezoneHelper.adjustTime(st, timezoneOffset),
                        endTime = TimezoneHelper.adjustTime(et, timezoneOffset),
                        startDatetime = "${current.date}T$st:00",
                        endDatetime = "${current.date}T$et:00",
                        remainingMinutes = remaining,
                        progressPercent = progress
                    )
                )
            }

            items.sortWith(
                compareBy<NowAiringItem> { getContentBrowseTier(it.contentType, it.title, it.titleEn, it.channelName) }
                    .thenBy { it.startDatetime }
            )

            Result.success(items)
        } catch (e: Exception) {
            android.util.Log.e("TvGuideRepository", "getNowAiring error: ${e.message}", e)
            Result.success(emptyList())
        }
    }

    suspend fun getNextAiring(includePaid: Boolean = false, timezoneOffset: Int = 0): Result<List<NextAiringItem>> = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        val db = database ?: return@withContext Result.success(emptyList())

        try {
            val cal = Calendar.getInstance()
            val sdfDate = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
            val todayDateStr = sdfDate.format(cal.time)
            val sdfTime = SimpleDateFormat("HH:mm", Locale.getDefault())
            val nowTimeStr = sdfTime.format(cal.time)

            cal.add(Calendar.DAY_OF_MONTH, 1)
            val tomorrowDateStr = sdfDate.format(cal.time)

            val rawRows = db.getUpNextSchedules(todayDateStr, tomorrowDateStr, nowTimeStr)
            val groupedByChannel = rawRows.groupBy { it.channelId }
            val items = mutableListOf<NextAiringItem>()

            for ((chId, chRows) in groupedByChannel) {
                val ch = channelMap[chId] ?: continue
                if (isIgnoredChannel(chId, ch.displayName) || isIgnoredChannel(chId, ch.nameEn) || isIgnoredChannel(chId, ch.nameAr)) continue
                if (!includePaid && (paidChannelIds.contains(chId) || ch.isPaidChannel)) continue

                val nextShow = chRows.firstOrNull() ?: continue
                if (isEsportsChannelName(nextShow.title)) continue

                val title = nextShow.title.trim()
                val st = nextShow.startTime
                val et = nextShow.endTime ?: "14:00"
                val logo = ch?.logoUrl
                val poster = nextShow.poster
                val overview = nextShow.overview
                val rating = nextShow.rating ?: "7.5"
                val channelName = ch?.displayName ?: "قناة"
                val targetContentId = if (nextShow.showId > 0L) nextShow.showId else (nextShow.programId ?: title).hashCode().toLong()

                items.add(
                    NextAiringItem(
                        broadcastId = chId * 1000L + items.size,
                        channelId = chId,
                        channelName = channelName,
                        channelLogo = logo,
                        contentId = targetContentId,
                        title = title,
                        titleEn = nextShow.titleEn,
                        contentType = nextShow.programType,
                        releaseYear = 2024,
                        rating = rating,
                        posterPath = poster,
                        backdropPath = poster,
                        overview = overview,
                        startTime = TimezoneHelper.adjustTime(st, timezoneOffset),
                        endTime = TimezoneHelper.adjustTime(et, timezoneOffset),
                        startDatetime = "${nextShow.date}T$st:00",
                        endDatetime = "${nextShow.date}T$et:00"
                    )
                )
            }

            items.sortWith(
                compareBy<NextAiringItem> { getContentBrowseTier(it.contentType, it.title, it.titleEn, it.channelName) }
                    .thenBy { it.startDatetime }
            )

            Result.success(items)
        } catch (e: Exception) {
            android.util.Log.e("TvGuideRepository", "getNextAiring error: ${e.message}", e)
            Result.success(emptyList())
        }
    }

    suspend fun getMovies(category: String? = null, search: String? = null, includePaid: Boolean = false, timezoneOffset: Int = 0): Result<List<Content>> = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        val db = database ?: return@withContext Result.success(emptyList())

        try {
            val showSummaries = db.getShows(category, search, includePaid, limit = 150)
            val contentList = showSummaries.map { s ->
                val airings = if (!s.nearestDate.isNullOrBlank() && !s.nearestTime.isNullOrBlank()) {
                    val ch = channelMap[s.nearestChannelId]
                    val chName = ch?.displayName ?: (if (!s.nearestChannelName.isNullOrBlank() && s.nearestChannelName != "قناة") s.nearestChannelName else null) ?: "قناة"
                    listOf(
                        Airing(
                            broadcastId = s.nearestChannelId * 1000L,
                            channelId = s.nearestChannelId,
                            contentId = s.id,
                            title = s.title,
                            channelName = chName,
                            date = s.nearestDate,
                            startTime = TimezoneHelper.adjustTime(s.nearestTime, timezoneOffset),
                            endTime = null
                        )
                    )
                } else emptyList()

                Content(
                    id = s.id,
                    titleAr = s.title,
                    titleEn = s.titleEn,
                    originalTitle = s.titleEn,
                    contentType = s.programType,
                    releaseYear = 2024,
                    rating = s.rating ?: "7.5",
                    posterPath = s.poster,
                    backdropPath = s.poster,
                    overview = s.overview,
                    overviewAr = s.overview,
                    genres = listOf(s.programType),
                    cast = emptyList(),
                    airingsCount = s.airingsCount,
                    airings = airings
                )
            }

            Result.success(contentList)
        } catch (e: Exception) {
            android.util.Log.e("TvGuideRepository", "getMovies error: ${e.message}", e)
            Result.success(emptyList())
        }
    }

    fun getContentDetailsSync(id: Long, timezoneOffset: Int = 0): Content? {
        ensureDataLoaded()
        val db = database ?: return null
        return try {
            val show = db.getShowByIdOrProgramId(showId = id, programId = null, title = null) ?: return null
            val rawAirings = db.getShowAirings(show.programId, show.title)

            val airings = rawAirings.mapIndexed { idx, a ->
                val ch = channelMap[a.channelId]
                Airing(
                    broadcastId = a.channelId * 1000L + idx,
                    channelId = a.channelId,
                    contentId = show.id,
                    title = a.title,
                    channelName = ch?.displayName ?: "قناة",
                    channelLogo = ch?.logoUrl,
                    poster = a.poster ?: show.poster,
                    date = a.date,
                    startTime = TimezoneHelper.adjustTime(a.startTime, timezoneOffset),
                    endTime = a.endTime?.let { TimezoneHelper.adjustTime(it, timezoneOffset) },
                    startDatetime = "${a.date}T${a.startTime}:00",
                    endDatetime = a.endTime?.let { "${a.date}T$it:00" }
                )
            }

            Content(
                id = show.id,
                titleAr = show.title,
                titleEn = show.titleEn,
                originalTitle = show.titleEn,
                contentType = show.programType,
                releaseYear = 2024,
                rating = show.rating ?: "7.5",
                posterPath = show.poster,
                backdropPath = show.poster,
                overview = show.overview,
                overviewAr = show.overview,
                genres = listOf(show.programType),
                cast = emptyList(),
                airingsCount = airings.size,
                airings = airings
            )
        } catch (e: Exception) {
            android.util.Log.e("TvGuideRepository", "getContentDetailsSync error: ${e.message}", e)
            null
        }
    }

    fun updateShowCategory(showId: Long?, title: String?, newCategory: String): Boolean {
        val db = database ?: return false
        return db.updateShowCategory(showId, title, newCategory)
    }

    fun hideShow(title: String): Boolean {
        val db = database ?: return false
        return db.hideShow(title)
    }

    suspend fun getContentDetails(id: Long, timezoneOffset: Int = 0): Result<Content> = withContext(Dispatchers.IO) {
        val found = getContentDetailsSync(id, timezoneOffset)
        if (found != null) Result.success(found)
        else Result.failure(Exception("Content not found"))
    }

    fun getChannelScheduleSync(channelId: Long, timezoneOffset: Int = 0): List<Airing> {
        ensureDataLoaded()
        val db = database ?: return emptyList()
        return try {
            val rawAirings = db.getChannelFullSchedule(channelId)
            val ch = channelMap[channelId]

            rawAirings.mapIndexed { idx, a ->
                Airing(
                    broadcastId = channelId * 1000L + idx,
                    channelId = channelId,
                    contentId = if (a.showId > 0L) a.showId else (a.programId ?: a.title).hashCode().toLong(),
                    title = a.title,
                    channelName = ch?.displayName ?: "قناة",
                    channelLogo = ch?.logoUrl,
                    poster = a.poster,
                    date = a.date,
                    startTime = TimezoneHelper.adjustTime(a.startTime, timezoneOffset),
                    endTime = a.endTime?.let { TimezoneHelper.adjustTime(it, timezoneOffset) },
                    startDatetime = "${a.date}T${a.startTime}:00",
                    endDatetime = a.endTime?.let { "${a.date}T$it:00" }
                )
            }
        } catch (e: Exception) {
            android.util.Log.e("TvGuideRepository", "getChannelScheduleSync error: ${e.message}", e)
            emptyList()
        }
    }

    suspend fun getChannelSchedule(channelId: Long, date: String? = null, timezoneOffset: Int = 0): Result<List<Airing>> = withContext(Dispatchers.IO) {
        Result.success(getChannelScheduleSync(channelId, timezoneOffset))
    }

    suspend fun searchAll(query: String, includePaid: Boolean = false, timezoneOffset: Int = 0): Result<SearchResults> = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        if (query.isBlank()) return@withContext Result.success(SearchResults())

        try {
            val qNorm = ArabicSearchHelper.normalizeArabic(query)

            var chSource = indexedChannels
            if (!includePaid) {
                chSource = chSource.filter { !it.isPaid }
            }
            val matchedChannels = chSource
                .filter { it.nameNorm.contains(qNorm) || it.nameEnNorm.contains(qNorm) || it.categoryNorm.contains(qNorm) }
                .map { it.channel }

            val db = database
            val matchedShows = if (db != null) {
                db.getShows(category = null, search = query, includePaid = includePaid, limit = 60).map { s ->
                    val airings = if (!s.nearestDate.isNullOrBlank() && !s.nearestTime.isNullOrBlank()) {
                        listOf(
                            Airing(
                                broadcastId = s.nearestChannelId * 1000L,
                                channelId = s.nearestChannelId,
                                contentId = s.id,
                                title = s.title,
                                channelName = s.nearestChannelName ?: "قناة",
                                date = s.nearestDate,
                                startTime = TimezoneHelper.adjustTime(s.nearestTime, timezoneOffset),
                                endTime = null
                            )
                        )
                    } else emptyList()

                    Content(
                        id = s.id,
                        titleAr = s.title,
                        titleEn = s.titleEn,
                        originalTitle = s.titleEn,
                        contentType = s.programType,
                        releaseYear = 2024,
                        rating = s.rating ?: "7.5",
                        posterPath = s.poster,
                        backdropPath = s.poster,
                        overview = s.overview,
                        overviewAr = s.overview,
                        genres = listOf(s.programType),
                        cast = emptyList(),
                        airingsCount = s.airingsCount,
                        airings = airings
                    )
                }
            } else emptyList()

            Result.success(SearchResults(channels = matchedChannels, shows = matchedShows))
        } catch (e: Exception) {
            android.util.Log.e("TvGuideRepository", "searchAll error: ${e.message}", e)
            Result.success(SearchResults())
        }
    }

    suspend fun search(query: String, includePaid: Boolean = false, timezoneOffset: Int = 0): Result<List<Content>> = withContext(Dispatchers.IO) {
        getMovies(search = query, includePaid = includePaid, timezoneOffset = timezoneOffset)
    }

    suspend fun syncLatestSchedulesOnline(force: Boolean = false): Boolean = withContext(Dispatchers.IO) {
        val db = database ?: return@withContext false
        ensureDataLoaded()
        try {
            val client = okhttp3.OkHttpClient.Builder()
                .connectTimeout(15, java.util.concurrent.TimeUnit.SECONDS)
                .readTimeout(25, java.util.concurrent.TimeUnit.SECONDS)
                .build()

            val metaUrl = "https://raw.githubusercontent.com/khalidfigo43/tv-guide-releases/main/data/metadata.json"
            val metaReq = okhttp3.Request.Builder().url(metaUrl).build()
            val metaResponse = client.newCall(metaReq).execute()
            if (!metaResponse.isSuccessful) return@withContext false
            val metaStr = metaResponse.body?.string() ?: return@withContext false
            val remoteMeta = json.decodeFromString<RemoteMetadata>(metaStr)

            val localVersion = db.getLocalVersion()
            val remoteVersion = remoteMeta.version

            // Check if local database is expired or has empty schedules for today
            val cairoTz = java.util.TimeZone.getTimeZone("Africa/Cairo")
            val sdf = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US).apply { timeZone = cairoTz }
            val todayStr = sdf.format(java.util.Date())
            val maxDate = db.getMaxScheduleDate()
            val todayCount = db.getSchedulesCountForDate(todayStr)
            val isExpiredOrEmpty = maxDate == null || maxDate < todayStr || todayCount < 30

            val shouldSync = force || isExpiredOrEmpty || (remoteVersion > localVersion)
            if (!shouldSync && localVersion > 0) {
                android.util.Log.i("TvGuideSync", "Local version $localVersion is up-to-date with remote $remoteVersion. No sync needed.")
                return@withContext false
            }

            android.util.Log.i("TvGuideSync", "Initiating sync: localVer=$localVersion, remoteVer=$remoteVersion, isExpired=$isExpiredOrEmpty, force=$force")

            // 1. Try Incremental Delta if applicable and not expired
            val deltaInfo = remoteMeta.delta
            if (!isExpiredOrEmpty && deltaInfo != null && deltaInfo.availableFrom == localVersion && deltaInfo.url.isNotBlank()) {
                try {
                    android.util.Log.i("TvGuideSync", "Attempting delta update from ${deltaInfo.url}...")
                    val deltaReq = okhttp3.Request.Builder().url(deltaInfo.url).build()
                    client.newCall(deltaReq).execute().use { dResp ->
                        if (dResp.isSuccessful) {
                            val dStr = dResp.body?.string()
                            if (!dStr.isNullOrBlank()) {
                                val deltaPayload = json.decodeFromString<DeltaPayload>(dStr)
                                val applied = db.applyDelta(deltaPayload, channelMap)
                                if (applied) {
                                    android.util.Log.i("TvGuideSync", "Delta update applied successfully to version ${deltaPayload.version}!")
                                    return@withContext true
                                }
                            }
                        }
                    }
                } catch (e: Throwable) {
                    android.util.Log.w("TvGuideSync", "Delta update failed: ${e.message}. Proceeding to full sync fallback.")
                }
            }

            // 2. Full Sync Fallback: Download full schedules snapshot
            android.util.Log.i("TvGuideSync", "Fetching full schedules snapshot from $liveUpdateUrl...")
            try {
                val fullReq = okhttp3.Request.Builder().url(liveUpdateUrl).build()
                client.newCall(fullReq).execute().use { fullResp ->
                    if (fullResp.isSuccessful) {
                        val fullStr = fullResp.body?.string()
                        if (!fullStr.isNullOrBlank()) {
                            val fullSchedules = json.decodeFromString<List<RawScheduleItem>>(fullStr)
                            if (fullSchedules.isNotEmpty()) {
                                db.applyFullSnapshot(
                                    schedules = fullSchedules,
                                    programs = null,
                                    version = remoteVersion,
                                    channelsMap = channelMap
                                )
                                android.util.Log.i("TvGuideSync", "Successfully applied full schedule snapshot with ${fullSchedules.size} items (version $remoteVersion)!")
                                return@withContext true
                            }
                        }
                    } else {
                        android.util.Log.w("TvGuideSync", "Full sync HTTP error: code ${fullResp.code}")
                    }
                }
            } catch (e: Throwable) {
                android.util.Log.e("TvGuideSync", "Full schedule sync failed: ${e.message}", e)
            }
        } catch (e: Throwable) {
            android.util.Log.w("TvGuideSync", "Sync completed with error: ${e.message}")
        }
        return@withContext false
    }
}
