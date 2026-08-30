package com.tvguide.app.data.repository

import android.content.Context
import com.tvguide.app.data.api.TvGuideApi
import com.tvguide.app.data.models.*
import com.tvguide.app.util.ArabicSearchHelper
import com.tvguide.app.util.TimezoneHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import java.io.File
import java.text.SimpleDateFormat
import java.util.*

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
    val is_paid: Boolean = false
)

data class IndexedShow(
    val id: Long,
    val titleNorm: String,
    val titleEnNorm: String,
    val channelNorm: String,
    val castNorm: List<String>,
    val channelIds: Set<Long>,
    val content: Content,
    val freeContent: Content,
    val isPaidOnly: Boolean,
    val hasFreeAirings: Boolean
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

    private var cachedChannels: List<Channel> = emptyList()
    private var cachedSchedules: List<RawScheduleItem> = emptyList()
    private var allShowsList: List<Content> = emptyList()
    private var showTitleToIdMap: Map<String, Long> = emptyMap()
    private var showIdToContentMap: Map<Long, Content> = emptyMap()
    private var paidChannelIds: Set<Long> = emptySet()
    
    // Fast Pre-indexed Search structures
    private var indexedShows: List<IndexedShow> = emptyList()
    private var indexedChannels: List<IndexedChannel> = emptyList()
    
    private var isLoaded: Boolean = false

    var liveUpdateUrl: String = "https://raw.githubusercontent.com/tvguide-live/data/main/all_channels_schedule.json"

    private fun isPaidChannelName(name: String?): Boolean {
        if (name.isNullOrBlank()) return false
        val n = name.lowercase()
        return n.contains("osn") ||
               n.contains("أو إس إن") ||
               n.contains("او اس ان") ||
               n.contains("أوسن") ||
               n.contains("اوسن") ||
               n.contains("ياهلا") ||
               n.contains("يا هلا") ||
               n.contains("bein") ||
               n.contains("بي ان") ||
               n.contains("بي إن") ||
               n.contains("alfa") ||
               n.contains("ألفا") ||
               n.contains("الفا") ||
               n.contains("mbc+") ||
               n.contains("mbc +") ||
               n.contains("دراما +") ||
               n.contains("دراما+") ||
               n.contains("showcase") ||
               n.contains("mezze") ||
               n.contains("iqiyi") ||
               n.contains("pop up")
    }

    private fun isAiringPaid(a: RawScheduleItem, channelMap: Map<Long, Channel>): Boolean {
        if (a.is_paid) return true
        if (a.channelId != null && paidChannelIds.contains(a.channelId)) return true
        if (a.channelId != null && channelMap[a.channelId]?.isPaidChannel == true) return true
        return isPaidChannelName(a.channelName)
    }

    private fun getContentTypePriority(type: String?, title: String?, channelName: String?): Int {
        val t = (type ?: "").lowercase()
        val tit = (title ?: "").lowercase()
        val ch = (channelName ?: "").lowercase()

        // 1. Movies (أفلام)
        if (t.contains("movie") || t.contains("film") || t.contains("cinema") ||
            tit.startsWith("فيلم") || tit.startsWith("فلم") ||
            ch.contains("cinema") || ch.contains("سينما") || ch.contains("movies") || ch.contains("افلام") || ch.contains("أفلام")) {
            return 1
        }

        // 2. Series (مسلسلات)
        if (t.contains("series") || t.contains("مسلسل") || t.contains("drama") || t.contains("دراما") || t.contains("episode") ||
            tit.startsWith("مسلسل") || tit.contains("حلقة") || tit.contains("الحلقة") ||
            ch.contains("drama") || ch.contains("دراما") || ch.contains("series") || ch.contains("مسلسلات")) {
            return 2
        }

        // 3. Theatre (مسرحيات)
        if (t.contains("theatre") || t.contains("مسرح") || tit.startsWith("مسرحية")) {
            return 3
        }

        // 4. Programs, Sports, Shows, Variety (برامج ومنوعات وأخرى)
        return 4
    }

    private fun ensureDataLoaded() {
        if (isLoaded || context == null) return
        try {
            // 1. Fast Load Channels
            val internalChannelsFile = File(context.filesDir, "channels.json")
            val chStr = if (internalChannelsFile.exists()) {
                internalChannelsFile.readText(Charsets.UTF_8)
            } else {
                context.assets.open("channels.json").bufferedReader().use { it.readText() }
            }
            cachedChannels = json.decodeFromString<List<Channel>>(chStr)
            paidChannelIds = cachedChannels.filter { it.isPaidChannel }.map { it.id }.toSet()

            // 2. Fast Load Schedules
            val internalSchedFile = File(context.filesDir, "schedules.json")
            val schStr = if (internalSchedFile.exists()) {
                internalSchedFile.readText(Charsets.UTF_8)
            } else {
                context.assets.open("schedules.json").bufferedReader().use { it.readText() }
            }
            cachedSchedules = json.decodeFromString<List<RawScheduleItem>>(schStr)

            // 3. Pre-build Master Shows List and Fast Search Index
            buildMasterShowsAndIndex()

            isLoaded = true
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private fun buildMasterShowsAndIndex() {
        val distinctTitles = cachedSchedules
            .filter { !it.title.isNullOrBlank() }
            .groupBy { it.title!!.trim() }

        val contentList = mutableListOf<Content>()
        val showsIndex = mutableListOf<IndexedShow>()
        val titleIdMap = mutableMapOf<String, Long>()
        val idContentMap = mutableMapOf<Long, Content>()
        val channelMap = cachedChannels.associateBy { it.id }
        var idCounter = 1L

        for ((title, airingsList) in distinctTitles) {
            val showId = idCounter++
            titleIdMap[title] = showId
            
            val freeAiringsList = airingsList.filter { !isAiringPaid(it, channelMap) }
            val hasFreeAirings = freeAiringsList.isNotEmpty()
            val isPaidOnly = freeAiringsList.isEmpty()

            val primaryAiring = if (hasFreeAirings) freeAiringsList.first() else airingsList.first()
            val castList = primaryAiring.cast
            val poster = primaryAiring.poster
            val channelIdsInShow = airingsList.mapNotNull { it.channelId }.toSet()

            val allAirings = airingsList.mapIndexed { idx, a ->
                val ch = a.channelId?.let { channelMap[it] }
                Airing(
                    broadcastId = showId * 100 + idx,
                    channelId = a.channelId ?: 1L,
                    contentId = showId,
                    title = title,
                    channelName = a.channelName ?: ch?.displayName ?: "قناة",
                    channelLogo = a.channelLogo ?: ch?.logoUrl,
                    poster = a.poster,
                    date = a.date ?: "اليوم",
                    startTime = a.startTime ?: "12:00",
                    endTime = a.endTime ?: "14:00",
                    startDatetime = "${a.date ?: "2026-08-30"}T${a.startTime ?: "12:00"}:00",
                    endDatetime = "${a.date ?: "2026-08-30"}T${a.endTime ?: "14:00"}:00"
                )
            }

            val freeAiringsMapped = freeAiringsList.mapIndexed { idx, a ->
                val ch = a.channelId?.let { channelMap[it] }
                Airing(
                    broadcastId = showId * 100 + idx,
                    channelId = a.channelId ?: 1L,
                    contentId = showId,
                    title = title,
                    channelName = a.channelName ?: ch?.displayName ?: "قناة",
                    channelLogo = a.channelLogo ?: ch?.logoUrl,
                    poster = a.poster,
                    date = a.date ?: "اليوم",
                    startTime = a.startTime ?: "12:00",
                    endTime = a.endTime ?: "14:00",
                    startDatetime = "${a.date ?: "2026-08-30"}T${a.startTime ?: "12:00"}:00",
                    endDatetime = "${a.date ?: "2026-08-30"}T${a.endTime ?: "14:00"}:00"
                )
            }

            val fullContent = Content(
                id = showId,
                titleAr = title,
                titleEn = primaryAiring.title_en,
                originalTitle = primaryAiring.title_en,
                contentType = primaryAiring.programType ?: "movie",
                releaseYear = 2024,
                rating = primaryAiring.rating ?: "7.8",
                posterPath = poster,
                backdropPath = poster,
                overview = primaryAiring.overview,
                overviewAr = primaryAiring.overview,
                genres = listOf("دراما", "منوعات"),
                cast = castList,
                airingsCount = airingsList.size,
                airings = allAirings
            )

            val freeContent = fullContent.copy(
                airingsCount = freeAiringsMapped.size,
                airings = freeAiringsMapped
            )

            contentList.add(fullContent)
            idContentMap[showId] = fullContent

            // Index show for instant O(1) matching
            showsIndex.add(
                IndexedShow(
                    id = fullContent.id,
                    titleNorm = ArabicSearchHelper.normalizeArabic(title),
                    titleEnNorm = ArabicSearchHelper.normalizeArabic(primaryAiring.title_en),
                    channelNorm = ArabicSearchHelper.normalizeArabic(primaryAiring.channelName),
                    castNorm = castList.map { ArabicSearchHelper.normalizeArabic(it.name) },
                    channelIds = channelIdsInShow,
                    content = fullContent,
                    freeContent = freeContent,
                    isPaidOnly = isPaidOnly,
                    hasFreeAirings = hasFreeAirings
                )
            )
        }

        allShowsList = contentList
        indexedShows = showsIndex
        showTitleToIdMap = titleIdMap
        showIdToContentMap = idContentMap

        // Pre-index channels
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
    }

    fun getContentDetailsSync(id: Long, timezoneOffset: Int = 0): Content? {
        ensureDataLoaded()
        val original = showIdToContentMap[id] ?: allShowsList.firstOrNull { it.id == id } ?: return null
        if (timezoneOffset == 0) return original

        return original.copy(
            airings = original.airings.map { a ->
                a.copy(
                    startTime = TimezoneHelper.adjustTime(a.startTime, timezoneOffset),
                    endTime = TimezoneHelper.adjustTime(a.endTime, timezoneOffset)
                )
            }
        )
    }

    suspend fun getChannels(category: String? = null, includePaid: Boolean = false): Result<List<Channel>> = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        var list = cachedChannels
        if (!includePaid) {
            list = list.filter { !it.isPaidChannel }
        }
        if (!category.isNullOrBlank() && category != "all") {
            list = list.filter { it.category.equals(category, ignoreCase = true) }
        }
        Result.success(list)
    }

    suspend fun getNowAiring(includePaid: Boolean = false, timezoneOffset: Int = 0): Result<List<NowAiringItem>> = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        val cal = Calendar.getInstance()
        val sdfTime = SimpleDateFormat("HH:mm", Locale.getDefault())
        val currentTimeStr = sdfTime.format(cal.time)
        val curMinutes = cal.get(Calendar.HOUR_OF_DAY) * 60 + cal.get(Calendar.MINUTE)

        val items = mutableListOf<NowAiringItem>()
        val groupedByChannel = cachedSchedules.groupBy { it.channelId ?: 0L }

        for ((chId, scheds) in groupedByChannel) {
            if (chId == 0L) continue
            val ch = cachedChannels.firstOrNull { it.id == chId }
            if (!includePaid && (paidChannelIds.contains(chId) || ch?.isPaidChannel == true)) continue

            // Find current show
            val current = scheds.firstOrNull { s ->
                val st = s.startTime ?: ""
                val et = s.endTime ?: ""
                if (st.isNotBlank() && et.isNotBlank()) {
                    if (et > st) currentTimeStr >= st && currentTimeStr < et
                    else currentTimeStr >= st || currentTimeStr < et
                } else false
            } ?: scheds.firstOrNull()

            if (current != null) {
                if (!includePaid && isPaidChannelName(current.channelName)) continue
                val title = (current.title ?: "بث مباشر").trim()
                val st = current.startTime ?: "12:00"
                val et = current.endTime ?: "13:00"
                val logo = current.channelLogo ?: ch?.logoUrl
                val poster = current.poster
                val channelName = current.channelName ?: ch?.displayName ?: "قناة"

                // Compute progress
                val sParts = st.split(":").mapNotNull { it.toIntOrNull() }
                val eParts = et.split(":").mapNotNull { it.toIntOrNull() }
                val sMinutes = if (sParts.size >= 2) sParts[0] * 60 + sParts[1] else curMinutes - 15
                var eMinutes = if (eParts.size >= 2) eParts[0] * 60 + eParts[1] else curMinutes + 45
                if (eMinutes <= sMinutes) eMinutes += 24 * 60
                val totalDuration = (eMinutes - sMinutes).coerceAtLeast(1)
                val elapsed = (curMinutes - sMinutes).coerceIn(0, totalDuration)
                val progress = ((elapsed * 100) / totalDuration).coerceIn(5, 95)
                val remaining = (eMinutes - curMinutes).coerceIn(1, 180)

                val targetContentId = showTitleToIdMap[title] ?: allShowsList.firstOrNull { it.titleAr == title }?.id ?: 1L

                items.add(
                    NowAiringItem(
                        broadcastId = chId * 1000L + items.size,
                        channelId = chId,
                        channelName = channelName,
                        channelLogo = logo,
                        contentId = targetContentId,
                        title = title,
                        titleEn = current.title_en,
                        contentType = current.programType ?: "movie",
                        releaseYear = 2024,
                        rating = current.rating ?: "7.5",
                        posterPath = poster,
                        backdropPath = poster,
                        overview = current.overview,
                        startTime = TimezoneHelper.adjustTime(st, timezoneOffset),
                        endTime = TimezoneHelper.adjustTime(et, timezoneOffset),
                        startDatetime = "${current.date ?: "2026-08-30"}T$st:00",
                        endDatetime = "${current.date ?: "2026-08-30"}T$et:00",
                        remainingMinutes = remaining,
                        progressPercent = progress
                    )
                )
            }
        }

        // Ordered by: 1. Movies -> 2. Series -> 3. Theatre -> 4. Programs/Sports/Other
        items.sortWith(
            compareBy<NowAiringItem> { getContentTypePriority(it.contentType, it.title, it.channelName) }
                .thenByDescending { it.progressPercent }
        )

        Result.success(items)
    }

    suspend fun getNextAiring(includePaid: Boolean = false, timezoneOffset: Int = 0): Result<List<NextAiringItem>> = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        val cal = Calendar.getInstance()
        val sdfTime = SimpleDateFormat("HH:mm", Locale.getDefault())
        val sdfDate = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
        val currentTimeStr = sdfTime.format(cal.time)
        val currentDateStr = sdfDate.format(cal.time)

        val items = mutableListOf<NextAiringItem>()
        val groupedByChannel = cachedSchedules.groupBy { it.channelId ?: 0L }

        for ((chId, scheds) in groupedByChannel) {
            if (chId == 0L) continue
            val ch = cachedChannels.firstOrNull { it.id == chId }
            if (!includePaid && (paidChannelIds.contains(chId) || ch?.isPaidChannel == true)) continue

            val currentIndex = scheds.indexOfFirst { s ->
                val st = s.startTime ?: ""
                val et = s.endTime ?: ""
                if (st.isNotBlank() && et.isNotBlank()) {
                    if (et > st) currentTimeStr >= st && currentTimeStr < et
                    else currentTimeStr >= st || currentTimeStr < et
                } else false
            }

            val next = if (currentIndex in 0 until scheds.size - 1) scheds[currentIndex + 1]
                       else scheds.getOrNull(1) ?: scheds.firstOrNull()

            if (next != null) {
                if (!includePaid && isPaidChannelName(next.channelName)) continue
                val title = (next.title ?: "برنامج قادم").trim()
                val st = next.startTime ?: "13:00"
                val et = next.endTime ?: "14:00"
                val logo = next.channelLogo ?: ch?.logoUrl
                val poster = next.poster
                val channelName = next.channelName ?: ch?.displayName ?: "قناة"

                val targetContentId = showTitleToIdMap[title] ?: allShowsList.firstOrNull { it.titleAr == title }?.id ?: 1L

                items.add(
                    NextAiringItem(
                        broadcastId = chId * 1000L + items.size,
                        channelId = chId,
                        channelName = channelName,
                        channelLogo = logo,
                        contentId = targetContentId,
                        title = title,
                        titleEn = next.title_en,
                        contentType = next.programType ?: "movie",
                        releaseYear = 2024,
                        rating = next.rating ?: "7.5",
                        posterPath = poster,
                        backdropPath = poster,
                        overview = next.overview,
                        startTime = TimezoneHelper.adjustTime(st, timezoneOffset),
                        endTime = TimezoneHelper.adjustTime(et, timezoneOffset),
                        startDatetime = "${next.date ?: currentDateStr}T$st:00",
                        endDatetime = "${next.date ?: currentDateStr}T$et:00"
                    )
                )
            }
        }

        // Ordered by: 1. Movies -> 2. Series -> 3. Theatre -> 4. Programs/Sports/Other
        items.sortWith(
            compareBy<NextAiringItem> { getContentTypePriority(it.contentType, it.title, it.channelName) }
                .thenBy { it.startTime }
        )

        Result.success(items)
    }

    suspend fun getMovies(category: String? = null, search: String? = null, includePaid: Boolean = false, timezoneOffset: Int = 0): Result<List<Content>> = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        
        var sourceIndexed = indexedShows
        if (!includePaid) {
            sourceIndexed = sourceIndexed.filter { !it.isPaidOnly && it.hasFreeAirings }
        }

        if (!category.isNullOrBlank() && category != "all") {
            sourceIndexed = sourceIndexed.filter { it.content.contentType.equals(category, ignoreCase = true) }
        }

        if (!search.isNullOrBlank()) {
            val qNorm = ArabicSearchHelper.normalizeArabic(search)
            sourceIndexed = sourceIndexed.filter { 
                it.titleNorm.contains(qNorm) || it.titleEnNorm.contains(qNorm) || it.channelNorm.contains(qNorm) || it.castNorm.any { c -> c.contains(qNorm) }
            }
        }

        // Ordered by: 1. Movies -> 2. Series -> 3. Theatre -> 4. Programs/Sports/Other
        sourceIndexed = sourceIndexed.sortedWith(
            compareBy<IndexedShow> { getContentTypePriority(it.content.contentType, it.content.titleAr, null) }
                .thenByDescending { if (includePaid) it.content.airingsCount else it.freeContent.airingsCount }
        )

        val result = sourceIndexed.map { indexed ->
            val baseContent = if (includePaid) indexed.content else indexed.freeContent
            if (timezoneOffset == 0) baseContent
            else baseContent.copy(
                airings = baseContent.airings.map { a ->
                    a.copy(
                        startTime = TimezoneHelper.adjustTime(a.startTime, timezoneOffset),
                        endTime = TimezoneHelper.adjustTime(a.endTime, timezoneOffset)
                    )
                }
            )
        }
        Result.success(result)
    }

    /**
     * Ultra-fast in-memory instant search
     */
    suspend fun searchAll(query: String, includePaid: Boolean = false, timezoneOffset: Int = 0): Result<SearchResults> = withContext(Dispatchers.IO) {
        ensureDataLoaded()
        if (query.isBlank()) {
            return@withContext Result.success(SearchResults())
        }

        val qNorm = ArabicSearchHelper.normalizeArabic(query)

        // 1. Match channels
        var chSource = indexedChannels
        if (!includePaid) {
            chSource = chSource.filter { !it.isPaid }
        }
        val matchedChannels = chSource
            .filter { it.nameNorm.contains(qNorm) || it.nameEnNorm.contains(qNorm) || it.categoryNorm.contains(qNorm) }
            .map { it.channel }

        // 2. Match shows
        var showSource = indexedShows
        if (!includePaid) {
            showSource = showSource.filter { !it.isPaidOnly && it.hasFreeAirings }
        }
        val matchedShows = showSource
            .filter {
                it.titleNorm.contains(qNorm) ||
                it.titleEnNorm.contains(qNorm) ||
                it.channelNorm.contains(qNorm) ||
                it.castNorm.any { actor -> actor.contains(qNorm) }
            }
            .sortedWith(
                compareBy<IndexedShow> { getContentTypePriority(it.content.contentType, it.content.titleAr, null) }
            )
            .map { indexed ->
                val baseContent = if (includePaid) indexed.content else indexed.freeContent
                if (timezoneOffset == 0) baseContent
                else baseContent.copy(
                    airings = baseContent.airings.map { a ->
                        a.copy(
                            startTime = TimezoneHelper.adjustTime(a.startTime, timezoneOffset),
                            endTime = TimezoneHelper.adjustTime(a.endTime, timezoneOffset)
                        )
                    }
                )
            }

        Result.success(
            SearchResults(
                channels = matchedChannels,
                shows = matchedShows
            )
        )
    }

    suspend fun getContentDetails(id: Long, timezoneOffset: Int = 0): Result<Content> = withContext(Dispatchers.IO) {
        val found = getContentDetailsSync(id, timezoneOffset)
        if (found != null) Result.success(found)
        else Result.failure(Exception("Content not found"))
    }

    fun getChannelScheduleSync(channelId: Long, timezoneOffset: Int = 0): List<Airing> {
        ensureDataLoaded()
        val channelScheds = cachedSchedules.filter { it.channelId == channelId }
        val ch = cachedChannels.firstOrNull { it.id == channelId }

        return channelScheds.mapIndexed { idx, a ->
            val title = (a.title ?: "برنامج تلفزيوني").trim()
            val targetContentId = showTitleToIdMap[title] ?: allShowsList.firstOrNull { it.titleAr == title }?.id ?: (channelId * 1000L + idx)
            Airing(
                broadcastId = channelId * 1000L + idx,
                channelId = channelId,
                contentId = targetContentId,
                title = title,
                channelName = a.channelName ?: ch?.displayName ?: "قناة",
                channelLogo = a.channelLogo ?: ch?.logoUrl,
                poster = a.poster,
                date = a.date ?: "اليوم",
                startTime = TimezoneHelper.adjustTime(a.startTime ?: "12:00", timezoneOffset),
                endTime = TimezoneHelper.adjustTime(a.endTime ?: "14:00", timezoneOffset),
                startDatetime = "${a.date ?: "2026-08-30"}T${a.startTime ?: "12:00"}:00",
                endDatetime = "${a.date ?: "2026-08-30"}T${a.endTime ?: "14:00"}:00"
            )
        }
    }

    suspend fun getChannelSchedule(channelId: Long, date: String? = null, timezoneOffset: Int = 0): Result<List<Airing>> = withContext(Dispatchers.IO) {
        Result.success(getChannelScheduleSync(channelId, timezoneOffset))
    }

    suspend fun search(query: String, includePaid: Boolean = false, timezoneOffset: Int = 0): Result<List<Content>> = withContext(Dispatchers.IO) {
        getMovies(search = query, includePaid = includePaid, timezoneOffset = timezoneOffset)
    }
}
