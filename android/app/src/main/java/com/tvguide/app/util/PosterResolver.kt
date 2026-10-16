package com.tvguide.app.util

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import com.tvguide.app.data.db.TvGuideDatabase
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import java.net.URLEncoder
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.TimeUnit

/**
 * Multi-tiered poster resolver for Android TV Guide.
 *
 * Ordered from strongest to weakest:
 * Tier 1: Existing high-resolution TMDB or source artwork in database.
 * Tier 2: TMDB Arabic Search API (Movies & Series with Arabic titles).
 * Tier 3: TMDB Global Search API (English / Foreign / Translated titles).
 * Tier 4: TVMaze Search API (International TV series & syndication).
 * Tier 5: Wikipedia Pageimages API (Arabic/English cultural shows & theatrical plays).
 * Tier 6: Official Channel Logo (Guaranteed crisp fallback — never an empty card).
 */
object PosterResolver {
    private const val TMDB_API_KEY = "370c62b4ed6c4cc06e73e105868f4fd5"

    private val client = OkHttpClient.Builder()
        .connectTimeout(4, TimeUnit.SECONDS)
        .readTimeout(6, TimeUnit.SECONDS)
        .build()

    // Thread-safe in-memory cache to prevent redundant network lookups
    private val memoryCache = ConcurrentHashMap<String, String>()

    @Volatile
    private var dbInstance: TvGuideDatabase? = null

    fun setDatabase(db: TvGuideDatabase?) {
        dbInstance = db
    }

    fun getCached(title: String): String? {
        val clean = ArabicSearchHelper.normalizeArabic(title.trim().lowercase())
        return if (clean.isNotBlank()) memoryCache[clean] else null
    }

    suspend fun resolvePoster(
        title: String,
        existingPoster: String? = null,
        channelLogo: String? = null
    ): String? = withContext(Dispatchers.IO) {
        // 1. Tier 1: Existing poster
        if (!existingPoster.isNullOrBlank() && !existingPoster.startsWith("data:") && existingPoster != channelLogo) {
            return@withContext existingPoster
        }

        val clean = ArabicSearchHelper.normalizeArabic(title.trim().lowercase())
        if (clean.isBlank()) return@withContext channelLogo

        memoryCache[clean]?.let { return@withContext it }

        val stripped = title.replace(Regex("^(?:مسلسل|فيلم|برنامج|مسرحية|عرض|سهرة)\\s+"), "").trim()
        val queryTitle = if (stripped.length >= 2) stripped else title.trim()

        // 2. Tier 2: TMDB Arabic Search (ar-SA)
        val tmdbAr = searchTmdb(queryTitle, "ar-SA")
        if (!tmdbAr.isNullOrBlank()) {
            cacheAndPersist(clean, title, tmdbAr)
            return@withContext tmdbAr
        }

        // 3. Tier 3: TMDB Global Search (en-US / no language filter)
        val tmdbGlobal = searchTmdb(queryTitle, "en-US")
        if (!tmdbGlobal.isNullOrBlank()) {
            cacheAndPersist(clean, title, tmdbGlobal)
            return@withContext tmdbGlobal
        }

        // 4. Tier 4: TVMaze API Search (TV Series)
        val tvmaze = searchTvMaze(queryTitle)
        if (!tvmaze.isNullOrBlank()) {
            cacheAndPersist(clean, title, tvmaze)
            return@withContext tvmaze
        }

        // 5. Tier 5: Wikipedia Pageimages API
        val wiki = searchWikipedia(queryTitle)
        if (!wiki.isNullOrBlank()) {
            cacheAndPersist(clean, title, wiki)
            return@withContext wiki
        }

        // 6. Tier 6: Official Channel Logo fallback (Guaranteed no blank card)
        if (!channelLogo.isNullOrBlank()) {
            memoryCache[clean] = channelLogo
            return@withContext channelLogo
        }

        null
    }

    private fun cacheAndPersist(cacheKey: String, originalTitle: String, posterUrl: String) {
        memoryCache[cacheKey] = posterUrl
        try {
            dbInstance?.updatePosterForTitle(originalTitle, posterUrl)
        } catch (_: Exception) {}
    }

    private fun searchTmdb(title: String, language: String): String? {
        return try {
            val q = URLEncoder.encode(title, "UTF-8")
            val url = "https://api.themoviedb.org/3/search/multi?api_key=$TMDB_API_KEY&query=$q&language=$language"
            val req = Request.Builder().url(url).build()
            client.newCall(req).execute().use { resp ->
                if (resp.isSuccessful) {
                    val body = resp.body?.string() ?: return null
                    val json = JSONObject(body)
                    val results = json.optJSONArray("results") ?: return null
                    for (i in 0 until results.length()) {
                        val item = results.getJSONObject(i)
                        val p = item.optString("poster_path")
                        if (!p.isNullOrBlank() && p != "null") {
                            return "https://image.tmdb.org/t/p/w500$p"
                        }
                    }
                }
            }
            null
        } catch (_: Exception) {
            null
        }
    }

    private fun searchTvMaze(title: String): String? {
        return try {
            val q = URLEncoder.encode(title, "UTF-8")
            val url = "https://api.tvmaze.com/singlesearch/shows?q=$q"
            val req = Request.Builder().url(url).build()
            client.newCall(req).execute().use { resp ->
                if (resp.isSuccessful) {
                    val body = resp.body?.string() ?: return null
                    val json = JSONObject(body)
                    val imageObj = json.optJSONObject("image")
                    val original = imageObj?.optString("original") ?: imageObj?.optString("medium")
                    if (!original.isNullOrBlank() && original != "null") {
                        return original
                    }
                }
            }
            null
        } catch (_: Exception) {
            null
        }
    }

    private fun searchWikipedia(title: String): String? {
        return try {
            val q = URLEncoder.encode(title, "UTF-8")
            val url = "https://ar.wikipedia.org/w/api.php?action=query&titles=$q&prop=pageimages&format=json&pithumbsize=500"
            val req = Request.Builder()
                .url(url)
                .header("User-Agent", "TvGuideApp/1.0 (contact@tvguide.app)")
                .build()
            client.newCall(req).execute().use { resp ->
                if (resp.isSuccessful) {
                    val body = resp.body?.string() ?: return null
                    val json = JSONObject(body)
                    val query = json.optJSONObject("query") ?: return null
                    val pages = query.optJSONObject("pages") ?: return null
                    val keys = pages.keys()
                    while (keys.hasNext()) {
                        val pageObj = pages.getJSONObject(keys.next())
                        val thumb = pageObj.optJSONObject("thumbnail")
                        val src = thumb?.optString("source")
                        if (!src.isNullOrBlank() && src != "null") {
                            return src
                        }
                    }
                }
            }
            null
        } catch (_: Exception) {
            null
        }
    }
}

/**
 * Composable helper to remember and dynamically resolve show/movie posters.
 * Instantly renders existing poster or channel logo (no dark blank screen),
 * then updates asynchronously if a high-res poster is found.
 */
@Composable
fun rememberResolvedPoster(
    title: String,
    initialPoster: String?,
    channelLogo: String?
): String? {
    var posterState by remember(title, initialPoster, channelLogo) {
        val immediate = if (!initialPoster.isNullOrBlank() && !initialPoster.startsWith("data:") && initialPoster != channelLogo) {
            initialPoster
        } else {
            PosterResolver.getCached(title) ?: channelLogo
        }
        mutableStateOf(immediate)
    }

    LaunchedEffect(title, initialPoster, channelLogo) {
        val cached = PosterResolver.getCached(title)
        if (cached != null) {
            posterState = cached
        } else if (posterState == null || posterState == channelLogo) {
            val resolved = PosterResolver.resolvePoster(title, initialPoster, channelLogo)
            if (!resolved.isNullOrBlank()) {
                posterState = resolved
            }
        }
    }

    return posterState
}

