package com.tvguide.app.data.db

import android.content.ContentValues
import android.content.Context
import android.database.Cursor
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import com.tvguide.app.data.classifier.CanonicalContentType
import com.tvguide.app.data.classifier.ContentClassifier
import com.tvguide.app.data.models.Channel
import com.tvguide.app.data.repository.DeltaPayload
import com.tvguide.app.data.repository.RawProgramItem
import com.tvguide.app.data.repository.RawScheduleItem
import com.tvguide.app.util.ArabicSearchHelper
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import java.io.FileOutputStream

data class ScheduleWithMeta(
    val channelId: Long,
    val date: String,
    val startTime: String,
    val endTime: String?,
    val programId: String?,
    val title: String,
    val titleEn: String?,
    val programType: String,
    val priority: Int,
    val poster: String?,
    val overview: String?,
    val rating: String?,
    val showId: Long = 0L
)

data class ShowSummary(
    val id: Long,
    val programId: String,
    val title: String,
    val titleEn: String?,
    val programType: String,
    val priorityTier: Int,
    val poster: String?,
    val overview: String?,
    val rating: String?,
    val airingsCount: Int,
    val nearestDate: String?,
    val nearestTime: String?,
    val nearestChannelName: String?,
    val nearestChannelId: Long,
    val hasFreeAirings: Boolean,
    val isPaidOnly: Boolean
)

class TvGuideDatabase(private val context: Context) : SQLiteOpenHelper(context, DATABASE_NAME, null, DATABASE_VERSION) {

    private val json = Json { ignoreUnknownKeys = true; isLenient = true; coerceInputValues = true }

    companion object {
        const val DATABASE_NAME = "tvguide_local.db"
        const val DATABASE_VERSION = 8
        const val TABLE_SCHEDULES = "schedules"
        const val TABLE_PROGRAMS = "programs"
        const val TABLE_SHOWS = "shows"
        const val TABLE_SYNC_META = "sync_meta"
    }

    init {
        copyPreloadedDatabaseIfNeeded()
    }

    fun copyPreloadedDatabaseIfNeeded(force: Boolean = false) {
        try {
            val dbFile = context.getDatabasePath(DATABASE_NAME)
            var needsCopy = force || !dbFile.exists() || dbFile.length() == 0L

            if (!needsCopy) {
                // Verify that the existing database actually contains the valid schema, data, and posters
                try {
                    SQLiteDatabase.openDatabase(dbFile.path, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                        val c1 = db.rawQuery("SELECT name FROM sqlite_master WHERE type='table' AND name='$TABLE_SHOWS'", null)
                        val hasShows = c1.moveToFirst()
                        c1.close()

                        val c2 = db.rawQuery("SELECT name FROM sqlite_master WHERE type='table' AND name='$TABLE_SCHEDULES'", null)
                        val hasSchedules = c2.moveToFirst()
                        c2.close()

                        if (hasShows && hasSchedules) {
                            val c3 = db.rawQuery("SELECT COUNT(*) FROM $TABLE_SCHEDULES", null)
                            val count = if (c3.moveToFirst()) c3.getInt(0) else 0
                            c3.close()

                            val c4 = db.rawQuery("SELECT COUNT(*) FROM $TABLE_PROGRAMS WHERE poster IS NOT NULL AND poster != ''", null)
                            val postersCount = if (c4.moveToFirst()) c4.getInt(0) else 0
                            c4.close()

                            val c5 = db.rawQuery("SELECT COUNT(*) FROM $TABLE_SCHEDULES WHERE channel_id IN (91, 179, 196, 200, 203, 204, 216, 217, 234, 235, 236, 238, 239, 240, 241, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260)", null)
                            val deletedChannelsInDb = if (c5.moveToFirst()) c5.getInt(0) else 0
                            c5.close()

                            val c6 = db.rawQuery("SELECT COUNT(*) FROM $TABLE_SHOWS WHERE title IN ('الراي', 'الأخبار', 'العربية', 'الحدث') AND program_type = 'movie'", null)
                            val fakeMoviesInDb = if (c6.moveToFirst()) c6.getInt(0) else 0
                            c6.close()

                            val c7 = db.rawQuery("SELECT MAX(date) FROM $TABLE_SCHEDULES", null)
                            val maxDateInDb = if (c7.moveToFirst()) c7.getString(0) else null
                            c7.close()

                            val c8 = db.rawQuery("SELECT value FROM $TABLE_SYNC_META WHERE key = 'version'", null)
                            val verInDb = if (c8.moveToFirst()) c8.getString(0)?.toIntOrNull() ?: 0 else 0
                            c8.close()

                            val cairoTz = java.util.TimeZone.getTimeZone("Africa/Cairo")
                            val sdf = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.US).apply { timeZone = cairoTz }
                            val todayStr = sdf.format(java.util.Date())

                            if (count < 20000 || postersCount < 3500 || deletedChannelsInDb > 0 || fakeMoviesInDb > 0 ||
                                (maxDateInDb != null && maxDateInDb < todayStr) || verInDb < 108) {
                                needsCopy = true
                            }
                        } else {
                            needsCopy = true
                        }
                    }
                } catch (e: Exception) {
                    android.util.Log.w("TvGuideDatabase", "Database health check failed: ${e.message}, will overwrite with preloaded asset.")
                    needsCopy = true
                }
            }

            if (needsCopy) {
                android.util.Log.i("TvGuideDatabase", "Copying preloaded database asset to ${dbFile.path}...")
                val savedHidden = mutableListOf<String>()
                if (dbFile.exists()) {
                    try {
                        SQLiteDatabase.openDatabase(dbFile.path, null, SQLiteDatabase.OPEN_READONLY).use { oldDb ->
                            val cur = oldDb.rawQuery("SELECT title FROM hidden_shows", null)
                            while (cur.moveToNext()) {
                                val t = cur.getString(0)
                                if (!t.isNullOrBlank()) savedHidden.add(t)
                            }
                            cur.close()
                        }
                    } catch (ignored: Exception) {}
                }

                dbFile.parentFile?.mkdirs()
                close()
                if (dbFile.exists()) dbFile.delete()
                File("${dbFile.path}-wal").delete()
                File("${dbFile.path}-shm").delete()
                File("${dbFile.path}-journal").delete()

                context.assets.open("tvguide_preloaded.db").use { input ->
                    FileOutputStream(dbFile).use { output ->
                        val buffer = ByteArray(65536)
                        var bytesRead: Int
                        while (input.read(buffer).also { bytesRead = it } != -1) {
                            output.write(buffer, 0, bytesRead)
                        }
                        output.flush()
                    }
                }

                if (savedHidden.isNotEmpty()) {
                    try {
                        SQLiteDatabase.openDatabase(dbFile.path, null, SQLiteDatabase.OPEN_READWRITE).use { newDb ->
                            newDb.execSQL("CREATE TABLE IF NOT EXISTS hidden_shows (title TEXT PRIMARY KEY)")
                            for (title in savedHidden) {
                                val cv = ContentValues().apply { put("title", title) }
                                newDb.insertWithOnConflict("hidden_shows", null, cv, SQLiteDatabase.CONFLICT_IGNORE)
                            }
                        }
                    } catch (ignored: Exception) {}
                }

                android.util.Log.i("TvGuideDatabase", "Preloaded database copied successfully: ${dbFile.length()} bytes")
            }
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "Could not copy preloaded database: ${e.message}", e)
        }
    }

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS $TABLE_SCHEDULES (
                channel_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                program_id TEXT,
                title TEXT NOT NULL,
                title_en TEXT,
                program_type TEXT,
                PRIMARY KEY (channel_id, date, start_time)
            )
            """.trimIndent()
        )

        db.execSQL("CREATE INDEX IF NOT EXISTS idx_sched_ch_date ON $TABLE_SCHEDULES(channel_id, date)")
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_sched_date_time ON $TABLE_SCHEDULES(date, start_time)")
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_sched_program_id ON $TABLE_SCHEDULES(program_id)")
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_sched_title ON $TABLE_SCHEDULES(title)")

        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS $TABLE_PROGRAMS (
                program_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                title_en TEXT,
                program_type TEXT NOT NULL,
                priority INTEGER DEFAULT 4,
                poster TEXT,
                overview TEXT,
                rating TEXT,
                cast_json TEXT
            )
            """.trimIndent()
        )
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_prog_title ON $TABLE_PROGRAMS(title)")
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_prog_type ON $TABLE_PROGRAMS(program_type)")

        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS $TABLE_SHOWS (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                title_en TEXT,
                program_type TEXT NOT NULL,
                priority_tier INTEGER NOT NULL,
                poster TEXT,
                overview TEXT,
                rating TEXT,
                cast_json TEXT,
                airings_count INTEGER DEFAULT 0,
                nearest_date TEXT,
                nearest_time TEXT,
                nearest_channel_name TEXT,
                nearest_channel_id INTEGER,
                has_free_airings INTEGER DEFAULT 1,
                is_paid_only INTEGER DEFAULT 0,
                title_norm TEXT,
                title_en_norm TEXT,
                channel_norm TEXT,
                cast_norm TEXT
            )
            """.trimIndent()
        )
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_shows_category ON $TABLE_SHOWS(program_type, priority_tier)")
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_shows_priority ON $TABLE_SHOWS(priority_tier, airings_count DESC)")
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_shows_title_norm ON $TABLE_SHOWS(title_norm)")
        db.execSQL("CREATE INDEX IF NOT EXISTS idx_shows_program_id ON $TABLE_SHOWS(program_id)")

        db.execSQL(
            """
            CREATE TABLE IF NOT EXISTS $TABLE_SYNC_META (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """.trimIndent()
        )
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        android.util.Log.i("TvGuideDatabase", "Upgrading database from version $oldVersion to $newVersion")
        db.execSQL("DROP TABLE IF EXISTS $TABLE_SCHEDULES")
        db.execSQL("DROP TABLE IF EXISTS $TABLE_PROGRAMS")
        db.execSQL("DROP TABLE IF EXISTS $TABLE_SHOWS")
        db.execSQL("DROP TABLE IF EXISTS $TABLE_SYNC_META")
        onCreate(db)
        // Copy preloaded snapshot immediately after upgrade
        copyPreloadedDatabaseIfNeeded(force = true)
    }

    override fun onDowngrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) {
        onUpgrade(db, oldVersion, newVersion)
    }

    fun isDatabaseEmpty(): Boolean {
        return try {
            val db = readableDatabase
            val cursor = db.rawQuery("SELECT COUNT(*) FROM $TABLE_SCHEDULES LIMIT 1", null)
            var count = 0
            if (cursor.moveToFirst()) {
                count = cursor.getInt(0)
            }
            cursor.close()
            count == 0
        } catch (e: Exception) {
            true
        }
    }

    fun getLocalVersion(): Int {
        return try {
            val db = readableDatabase
            val cursor = db.rawQuery("SELECT value FROM $TABLE_SYNC_META WHERE key = 'version' LIMIT 1", null)
            var version = 0
            if (cursor.moveToFirst()) {
                version = cursor.getString(0)?.toIntOrNull() ?: 0
            }
            cursor.close()
            version
        } catch (e: Exception) {
            0
        }
    }

    fun setLocalVersion(version: Int) {
        try {
            val db = writableDatabase
            val cv = ContentValues().apply {
                put("key", "version")
                put("value", version.toString())
            }
            db.insertWithOnConflict(TABLE_SYNC_META, null, cv, SQLiteDatabase.CONFLICT_REPLACE)
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "Error setting version: ${e.message}")
        }
    }

    fun getMaxScheduleDate(): String? {
        return try {
            val db = readableDatabase
            val cursor = db.rawQuery("SELECT MAX(date) FROM $TABLE_SCHEDULES LIMIT 1", null)
            var maxDate: String? = null
            if (cursor.moveToFirst()) {
                maxDate = cursor.getString(0)
            }
            cursor.close()
            maxDate
        } catch (e: Exception) {
            null
        }
    }

    fun getSchedulesCountForDate(dateStr: String): Int {
        return try {
            val db = readableDatabase
            val cursor = db.rawQuery("SELECT COUNT(*) FROM $TABLE_SCHEDULES WHERE date = ? LIMIT 1", arrayOf(dateStr))
            var count = 0
            if (cursor.moveToFirst()) {
                count = cursor.getInt(0)
            }
            cursor.close()
            count
        } catch (e: Exception) {
            0
        }
    }

    // ---------------------------------------------------------------------------------------------
    // HIGH-PERFORMANCE SCREEN-SPECIFIC QUERIES (FAIL-SAFE)
    // ---------------------------------------------------------------------------------------------

    fun getLiveNowSchedules(todayStr: String, yesterdayStr: String, nowTimeStr: String): List<ScheduleWithMeta> {
        val list = mutableListOf<ScheduleWithMeta>()
        try {
            val db = readableDatabase
            val hiddenTitles = getHiddenShows()
            val sql = """
                SELECT s.channel_id, s.date, s.start_time, s.end_time, s.program_id, s.title, s.title_en, s.program_type,
                       COALESCE(p.poster, prog_title.poster, sh_p.poster, sh_t.poster) as poster,
                       COALESCE(p.overview, prog_title.overview, sh_p.overview, sh_t.overview) as overview,
                       COALESCE(p.rating, prog_title.rating, sh_p.rating, sh_t.rating, '7.5') as rating,
                       COALESCE(p.priority, prog_title.priority, sh_p.priority_tier, sh_t.priority_tier, 4) as priority,
                       COALESCE(sh_p.id, sh_t.id, 0) as show_id
                FROM $TABLE_SCHEDULES s
                LEFT JOIN $TABLE_PROGRAMS p ON s.program_id = p.program_id
                LEFT JOIN $TABLE_PROGRAMS prog_title ON s.title = prog_title.title
                LEFT JOIN $TABLE_SHOWS sh_p ON s.program_id = sh_p.program_id
                LEFT JOIN $TABLE_SHOWS sh_t ON s.title = sh_t.title
                WHERE (
                    (s.date = ? AND s.start_time <= ? AND (s.end_time > ? OR s.end_time < s.start_time))
                    OR
                    (s.date = ? AND s.end_time < s.start_time AND ? < s.end_time)
                )
                AND s.title NOT IN ('برنامج تلفزيوني', 'برنامج تليفزيوني', 'برنامج', 'منوعات', 'عرض')
                AND s.title NOT LIKE 'برامج %'
                AND s.title NOT LIKE 'فترة بث%'
                AND s.title NOT LIKE '%بث ليلي%'
                AND s.title NOT LIKE '%إعادة برامج%'
                AND s.title NOT LIKE '%اعادة برامج%'
                ORDER BY s.channel_id ASC, s.start_time DESC
            """.trimIndent()
            val cursor = db.rawQuery(sql, arrayOf(todayStr, nowTimeStr, nowTimeStr, yesterdayStr, nowTimeStr))
            while (cursor.moveToNext()) {
                val title = cursor.getString(5)
                if (hiddenTitles.contains(title)) continue
                list.add(
                    ScheduleWithMeta(
                        channelId = cursor.getLong(0),
                        date = cursor.getString(1),
                        startTime = cursor.getString(2),
                        endTime = cursor.getString(3),
                        programId = cursor.getString(4),
                        title = title,
                        titleEn = cursor.getString(6),
                        programType = cursor.getString(7) ?: "movie",
                        poster = cursor.getString(8),
                        overview = cursor.getString(9),
                        rating = cursor.getString(10) ?: "7.5",
                        priority = cursor.getInt(11),
                        showId = cursor.getLong(12)
                    )
                )
            }
            cursor.close()
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "getLiveNowSchedules error: ${e.message}", e)
            copyPreloadedDatabaseIfNeeded(force = true)
        }
        return list
    }

    fun getUpNextSchedules(todayStr: String, tomorrowStr: String, nowTimeStr: String): List<ScheduleWithMeta> {
        val list = mutableListOf<ScheduleWithMeta>()
        try {
            val db = readableDatabase
            val hiddenTitles = getHiddenShows()
            val sql = """
                SELECT s.channel_id, s.date, s.start_time, s.end_time, s.program_id, s.title, s.title_en, s.program_type,
                       COALESCE(p.poster, prog_title.poster, sh_p.poster, sh_t.poster) as poster,
                       COALESCE(p.overview, prog_title.overview, sh_p.overview, sh_t.overview) as overview,
                       COALESCE(p.rating, prog_title.rating, sh_p.rating, sh_t.rating, '7.5') as rating,
                       COALESCE(p.priority, prog_title.priority, sh_p.priority_tier, sh_t.priority_tier, 4) as priority,
                       COALESCE(sh_p.id, sh_t.id, 0) as show_id
                FROM (
                    SELECT channel_id, date, start_time, end_time, program_id, title, title_en, program_type,
                           ROW_NUMBER() OVER (PARTITION BY channel_id ORDER BY date ASC, start_time ASC) as rn
                    FROM $TABLE_SCHEDULES
                    WHERE ((date = ? AND start_time > ?) OR (date = ?))
                      AND title NOT IN ('برنامج تلفزيوني', 'برنامج تليفزيوني', 'برنامج', 'منوعات', 'عرض')
                      AND title NOT LIKE 'برامج %'
                      AND title NOT LIKE 'فترة بث%'
                      AND title NOT LIKE '%بث ليلي%'
                      AND title NOT LIKE '%إعادة برامج%'
                      AND title NOT LIKE '%اعادة برامج%'
                ) s
                LEFT JOIN $TABLE_PROGRAMS p ON s.program_id = p.program_id
                LEFT JOIN $TABLE_PROGRAMS prog_title ON s.title = prog_title.title
                LEFT JOIN $TABLE_SHOWS sh_p ON s.program_id = sh_p.program_id
                LEFT JOIN $TABLE_SHOWS sh_t ON s.title = sh_t.title
                WHERE s.rn = 1
                ORDER BY s.date ASC, s.start_time ASC
            """.trimIndent()
            val cursor = db.rawQuery(sql, arrayOf(todayStr, nowTimeStr, tomorrowStr))
            while (cursor.moveToNext()) {
                val title = cursor.getString(5)
                if (hiddenTitles.contains(title)) continue
                list.add(
                    ScheduleWithMeta(
                        channelId = cursor.getLong(0),
                        date = cursor.getString(1),
                        startTime = cursor.getString(2),
                        endTime = cursor.getString(3),
                        programId = cursor.getString(4),
                        title = title,
                        titleEn = cursor.getString(6),
                        programType = cursor.getString(7) ?: "movie",
                        poster = cursor.getString(8),
                        overview = cursor.getString(9),
                        rating = cursor.getString(10) ?: "7.5",
                        priority = cursor.getInt(11),
                        showId = cursor.getLong(12)
                    )
                )
            }
            cursor.close()
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "getUpNextSchedules error: ${e.message}", e)
        }
        return list
    }

    fun getShows(category: String?, search: String?, includePaid: Boolean, limit: Int = 150): List<ShowSummary> {
        val list = mutableListOf<ShowSummary>()
        try {
            val db = readableDatabase
            val whereClauses = mutableListOf<String>()
            val args = mutableListOf<String>()

            if (!includePaid) {
                whereClauses.add("has_free_airings = 1")
            }

            // Exclude unnamed placeholder shows from browse recommendations
            whereClauses.add("title NOT IN ('برنامج تلفزيوني', 'برنامج تليفزيوني', 'برنامج', 'منوعات', 'عرض')")
            whereClauses.add("title NOT LIKE 'برامج %'")
            whereClauses.add("title NOT LIKE 'فترة بث%'")
            whereClauses.add("title NOT LIKE '%بث ليلي%'")
            whereClauses.add("title NOT LIKE '%إعادة برامج%'")
            whereClauses.add("title NOT LIKE '%اعادة برامج%'")

            if (!category.isNullOrBlank() && category != "all") {
                when (category.lowercase().trim()) {
                    "movie", "أفلام", "افلام" -> {
                        whereClauses.add("program_type = 'movie'")
                    }
                    "series", "مسلسلات" -> {
                        whereClauses.add("program_type = 'series'")
                    }
                    "kids", "cartoon", "أطفال", "اطفال", "كرتون" -> {
                        whereClauses.add("program_type = 'cartoon'")
                    }
                    else -> {
                        whereClauses.add("program_type NOT IN ('movie', 'series', 'cartoon')")
                    }
                }
            }

            if (!search.isNullOrBlank()) {
                val qNorm = ArabicSearchHelper.normalizeArabic(search)
                whereClauses.add("(title_norm LIKE ? OR title_en_norm LIKE ? OR channel_norm LIKE ? OR cast_norm LIKE ?)")
                val likePattern = "%$qNorm%"
                args.add(likePattern)
                args.add(likePattern)
                args.add(likePattern)
                args.add(likePattern)
            }

            val whereStr = if (whereClauses.isNotEmpty()) "WHERE " + whereClauses.joinToString(" AND ") else ""
            val sql = """
                SELECT id, program_id, title, title_en, program_type, priority_tier, poster, overview, rating,
                       airings_count, nearest_date, nearest_time, nearest_channel_name, nearest_channel_id,
                       has_free_airings, is_paid_only
                FROM $TABLE_SHOWS
                $whereStr
                ORDER BY priority_tier ASC, airings_count DESC
                LIMIT $limit
            """.trimIndent()

            val hiddenTitles = getHiddenShows()
            val cursor = db.rawQuery(sql, if (args.isNotEmpty()) args.toTypedArray() else null)
            while (cursor.moveToNext()) {
                val title = cursor.getString(2)
                if (hiddenTitles.contains(title)) continue
                list.add(
                    ShowSummary(
                        id = cursor.getLong(0),
                        programId = cursor.getString(1),
                        title = title,
                        titleEn = cursor.getString(3),
                        programType = cursor.getString(4),
                        priorityTier = cursor.getInt(5),
                        poster = cursor.getString(6),
                        overview = cursor.getString(7),
                        rating = cursor.getString(8),
                        airingsCount = cursor.getInt(9),
                        nearestDate = cursor.getString(10),
                        nearestTime = cursor.getString(11),
                        nearestChannelName = cursor.getString(12),
                        nearestChannelId = cursor.getLong(13),
                        hasFreeAirings = cursor.getInt(14) == 1,
                        isPaidOnly = cursor.getInt(15) == 1
                    )
                )
            }
            cursor.close()
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "getShows error: ${e.message}", e)
            copyPreloadedDatabaseIfNeeded(force = true)
        }
        return list
    }

    fun getShowByIdOrProgramId(showId: Long?, programId: String?, title: String?): ShowSummary? {
        try {
            val db = readableDatabase

            // 1. Try finding by showId if positive
            if (showId != null && showId > 0) {
                val cursor = db.rawQuery(
                    "SELECT id, program_id, title, title_en, program_type, priority_tier, poster, overview, rating, airings_count, nearest_date, nearest_time, nearest_channel_name, nearest_channel_id, has_free_airings, is_paid_only FROM $TABLE_SHOWS WHERE id = ? LIMIT 1",
                    arrayOf(showId.toString())
                )
                if (cursor.moveToFirst()) {
                    val res = mapCursorToShowSummary(cursor)
                    cursor.close()
                    return res
                }
                cursor.close()
            }

            // 2. Try finding by programId
            if (!programId.isNullOrBlank()) {
                val cursor = db.rawQuery(
                    "SELECT id, program_id, title, title_en, program_type, priority_tier, poster, overview, rating, airings_count, nearest_date, nearest_time, nearest_channel_name, nearest_channel_id, has_free_airings, is_paid_only FROM $TABLE_SHOWS WHERE program_id = ? LIMIT 1",
                    arrayOf(programId)
                )
                if (cursor.moveToFirst()) {
                    val res = mapCursorToShowSummary(cursor)
                    cursor.close()
                    return res
                }
                cursor.close()
            }

            // 3. Try finding by title
            if (!title.isNullOrBlank()) {
                val cursor = db.rawQuery(
                    "SELECT id, program_id, title, title_en, program_type, priority_tier, poster, overview, rating, airings_count, nearest_date, nearest_time, nearest_channel_name, nearest_channel_id, has_free_airings, is_paid_only FROM $TABLE_SHOWS WHERE title = ? LIMIT 1",
                    arrayOf(title)
                )
                if (cursor.moveToFirst()) {
                    val res = mapCursorToShowSummary(cursor)
                    cursor.close()
                    return res
                }
                cursor.close()
            }

            // 4. Try matching hashCode if showId is arbitrary or negative
            if (showId != null && showId != 0L) {
                val cursor = db.rawQuery(
                    "SELECT id, program_id, title, title_en, program_type, priority_tier, poster, overview, rating, airings_count, nearest_date, nearest_time, nearest_channel_name, nearest_channel_id, has_free_airings, is_paid_only FROM $TABLE_SHOWS",
                    null
                )
                while (cursor.moveToNext()) {
                    val pid = cursor.getString(1) ?: ""
                    val tit = cursor.getString(2) ?: ""
                    if ((pid.ifBlank { tit }).hashCode().toLong() == showId || tit.hashCode().toLong() == showId) {
                        val res = mapCursorToShowSummary(cursor)
                        cursor.close()
                        return res
                    }
                }
                cursor.close()
            }

            // 5. Fallback: Synthesize ShowSummary from schedules table directly
            val targetTitle = title ?: ""
            if (targetTitle.isNotBlank() || showId != null) {
                val sCursor = if (targetTitle.isNotBlank()) {
                    db.rawQuery("SELECT channel_id, date, start_time, title, title_en, program_type, program_id FROM $TABLE_SCHEDULES WHERE title = ? LIMIT 1", arrayOf(targetTitle))
                } else {
                    db.rawQuery("SELECT channel_id, date, start_time, title, title_en, program_type, program_id FROM $TABLE_SCHEDULES LIMIT 500", null)
                }

                while (sCursor.moveToNext()) {
                    val sTitle = sCursor.getString(3) ?: ""
                    val sPid = sCursor.getString(6) ?: ""
                    val matches = if (targetTitle.isNotBlank()) sTitle == targetTitle else ((sPid.ifBlank { sTitle }).hashCode().toLong() == showId || sTitle.hashCode().toLong() == showId)
                    if (matches) {
                        val chId = sCursor.getLong(0)
                        val dt = sCursor.getString(1)
                        val st = sCursor.getString(2)
                        val tEn = sCursor.getString(4)
                        val pType = sCursor.getString(5) ?: "movie"
                        sCursor.close()
                        return ShowSummary(
                            id = showId ?: sTitle.hashCode().toLong(),
                            programId = sPid.ifBlank { "prog_${sTitle.hashCode()}" },
                            title = sTitle,
                            titleEn = tEn,
                            programType = pType,
                            priorityTier = if (pType == "movie") 1 else if (pType == "series") 2 else if (pType == "cartoon") 3 else 4,
                            poster = null,
                            overview = null,
                            rating = "7.5",
                            airingsCount = 1,
                            nearestDate = dt,
                            nearestTime = st,
                            nearestChannelName = "قناة",
                            nearestChannelId = chId,
                            hasFreeAirings = true,
                            isPaidOnly = false
                        )
                    }
                }
                sCursor.close()
            }
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "getShowByIdOrProgramId error: ${e.message}", e)
        }
        return null
    }

    private fun mapCursorToShowSummary(cursor: Cursor): ShowSummary {
        return ShowSummary(
            id = cursor.getLong(0),
            programId = cursor.getString(1) ?: "",
            title = cursor.getString(2) ?: "",
            titleEn = cursor.getString(3),
            programType = cursor.getString(4) ?: "movie",
            priorityTier = cursor.getInt(5),
            poster = cursor.getString(6),
            overview = cursor.getString(7),
            rating = cursor.getString(8) ?: "7.5",
            airingsCount = cursor.getInt(9),
            nearestDate = cursor.getString(10),
            nearestTime = cursor.getString(11),
            nearestChannelName = cursor.getString(12),
            nearestChannelId = cursor.getLong(13),
            hasFreeAirings = cursor.getInt(14) == 1,
            isPaidOnly = cursor.getInt(15) == 1
        )
    }

    fun updateShowCategory(showId: Long?, title: String?, newCategory: String): Boolean {
        return try {
            val db = writableDatabase
            val tier = when (newCategory.lowercase().trim()) {
                "movie", "فيلم" -> 1
                "series", "مسلسل" -> 2
                "cartoon", "kids", "كارتون", "أطفال" -> 3
                else -> 4
            }
            val canonicalCat = when (tier) {
                1 -> "movie"
                2 -> "series"
                3 -> "cartoon"
                else -> "other"
            }

            if (showId != null && showId > 0) {
                db.execSQL("UPDATE $TABLE_SHOWS SET program_type = ?, priority_tier = ? WHERE id = ?", arrayOf(canonicalCat, tier, showId))
            }
            if (!title.isNullOrBlank()) {
                db.execSQL("UPDATE $TABLE_SHOWS SET program_type = ?, priority_tier = ? WHERE title = ?", arrayOf(canonicalCat, tier, title))
                db.execSQL("UPDATE $TABLE_PROGRAMS SET program_type = ?, priority = ? WHERE title = ?", arrayOf(canonicalCat, tier, title))
                db.execSQL("UPDATE $TABLE_SCHEDULES SET program_type = ? WHERE title = ?", arrayOf(canonicalCat, title))
            }
            true
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "updateShowCategory error: ${e.message}", e)
            false
        }
    }

    fun updatePosterForTitle(title: String, posterUrl: String) {
        if (title.isBlank() || posterUrl.isBlank()) return
        try {
            val db = writableDatabase
            val cvProg = ContentValues().apply {
                put("poster", posterUrl)
            }
            db.update(TABLE_PROGRAMS, cvProg, "title = ?", arrayOf(title))
            val cvShow = ContentValues().apply {
                put("poster", posterUrl)
            }
            db.update(TABLE_SHOWS, cvShow, "title = ?", arrayOf(title))
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "updatePosterForTitle error: ${e.message}")
        }
    }

    fun hideShow(title: String): Boolean {
        return try {
            val db = writableDatabase
            db.execSQL("CREATE TABLE IF NOT EXISTS hidden_shows (title TEXT PRIMARY KEY)")
            db.execSQL("INSERT OR REPLACE INTO hidden_shows (title) VALUES (?)", arrayOf(title.trim()))
            true
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "hideShow error: ${e.message}", e)
            false
        }
    }

    fun getHiddenShows(): Set<String> {
        val set = mutableSetOf<String>()
        try {
            val db = readableDatabase
            db.execSQL("CREATE TABLE IF NOT EXISTS hidden_shows (title TEXT PRIMARY KEY)")
            val cursor = db.rawQuery("SELECT title FROM hidden_shows", null)
            while (cursor.moveToNext()) {
                val t = cursor.getString(0)
                if (!t.isNullOrBlank()) set.add(t.trim())
            }
            cursor.close()
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "getHiddenShows error: ${e.message}", e)
        }
        return set
    }

    fun getShowAirings(programId: String?, title: String?): List<ScheduleWithMeta> {
        val list = mutableListOf<ScheduleWithMeta>()
        try {
            val db = readableDatabase
            val sql = """
                SELECT s.channel_id, s.date, s.start_time, s.end_time, s.program_id, s.title, s.title_en, s.program_type,
                       COALESCE(p.poster, prog_title.poster) as poster,
                       COALESCE(p.overview, prog_title.overview) as overview,
                       COALESCE(p.rating, prog_title.rating, '7.5') as rating,
                       COALESCE(p.priority, prog_title.priority, 4) as priority
                FROM $TABLE_SCHEDULES s
                LEFT JOIN $TABLE_PROGRAMS p ON s.program_id = p.program_id
                LEFT JOIN $TABLE_PROGRAMS prog_title ON s.title = prog_title.title
                WHERE (? IS NOT NULL AND s.program_id = ?) OR s.title = ?
                ORDER BY s.date ASC, s.start_time ASC
            """.trimIndent()
            val cursor = db.rawQuery(sql, arrayOf(programId, programId, title))
            while (cursor.moveToNext()) {
                list.add(
                    ScheduleWithMeta(
                        channelId = cursor.getLong(0),
                        date = cursor.getString(1),
                        startTime = cursor.getString(2),
                        endTime = cursor.getString(3),
                        programId = cursor.getString(4),
                        title = cursor.getString(5),
                        titleEn = cursor.getString(6),
                        programType = cursor.getString(7) ?: "movie",
                        poster = cursor.getString(8),
                        overview = cursor.getString(9),
                        rating = cursor.getString(10) ?: "7.5",
                        priority = cursor.getInt(11)
                    )
                )
            }
            cursor.close()
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "getShowAirings error: ${e.message}", e)
        }
        return list
    }

    fun getChannelFullSchedule(channelId: Long): List<ScheduleWithMeta> {
        val list = mutableListOf<ScheduleWithMeta>()
        try {
            val db = readableDatabase
            val sql = """
                SELECT s.channel_id, s.date, s.start_time, s.end_time, s.program_id, s.title, s.title_en, s.program_type,
                       COALESCE(p.poster, prog_title.poster, sh_p.poster, sh_t.poster) as poster,
                       COALESCE(p.overview, prog_title.overview, sh_p.overview, sh_t.overview) as overview,
                       COALESCE(p.rating, prog_title.rating, sh_p.rating, sh_t.rating, '7.5') as rating,
                       COALESCE(p.priority, prog_title.priority, sh_p.priority_tier, sh_t.priority_tier, 4) as priority,
                       COALESCE(sh_p.id, sh_t.id, 0) as show_id
                FROM $TABLE_SCHEDULES s
                LEFT JOIN $TABLE_PROGRAMS p ON s.program_id = p.program_id
                LEFT JOIN $TABLE_PROGRAMS prog_title ON s.title = prog_title.title
                LEFT JOIN $TABLE_SHOWS sh_p ON s.program_id = sh_p.program_id
                LEFT JOIN $TABLE_SHOWS sh_t ON s.title = sh_t.title
                WHERE s.channel_id = ?
                ORDER BY s.date ASC, s.start_time ASC
            """.trimIndent()
            val cursor = db.rawQuery(sql, arrayOf(channelId.toString()))
            while (cursor.moveToNext()) {
                list.add(
                    ScheduleWithMeta(
                        channelId = cursor.getLong(0),
                        date = cursor.getString(1),
                        startTime = cursor.getString(2),
                        endTime = cursor.getString(3),
                        programId = cursor.getString(4),
                        title = cursor.getString(5),
                        titleEn = cursor.getString(6),
                        programType = cursor.getString(7) ?: "movie",
                        poster = cursor.getString(8),
                        overview = cursor.getString(9),
                        rating = cursor.getString(10) ?: "7.5",
                        priority = cursor.getInt(11),
                        showId = cursor.getLong(12)
                    )
                )
            }
            cursor.close()
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "getChannelFullSchedule error: ${e.message}", e)
        }
        return list
    }

    // ---------------------------------------------------------------------------------------------
    // INCREMENTAL DELTA & SYNC UPDATES (CANONICAL SOURCE OF TRUTH)
    // ---------------------------------------------------------------------------------------------

    fun applyDelta(delta: DeltaPayload, channelsMap: Map<Long, Channel>): Boolean {
        val db = writableDatabase
        db.beginTransaction()
        try {
            val affectedProgramIds = mutableSetOf<String>()

            // 1. Process deletions
            if (delta.deleted.isNotEmpty()) {
                val delStmt = db.compileStatement("DELETE FROM $TABLE_SCHEDULES WHERE channel_id = ? AND date = ? AND start_time = ?")
                for (k in delta.deleted) {
                    try {
                        val c = db.rawQuery(
                            "SELECT program_id FROM $TABLE_SCHEDULES WHERE channel_id = ? AND date = ? AND start_time = ? LIMIT 1",
                            arrayOf(k.channelId.toString(), k.date, k.startTime)
                        )
                        if (c.moveToFirst()) {
                            c.getString(0)?.let { affectedProgramIds.add(it) }
                        }
                        c.close()

                        delStmt.clearBindings()
                        delStmt.bindLong(1, k.channelId)
                        delStmt.bindString(2, k.date)
                        delStmt.bindString(3, k.startTime)
                        delStmt.executeUpdateDelete()
                    } catch (e: Exception) {
                        android.util.Log.w("TvGuideDatabase", "Deletion error: ${e.message}")
                    }
                }
            }

            // 2. Process added & updated
            val itemsToUpsert = delta.added + delta.updated
            if (itemsToUpsert.isNotEmpty()) {
                val upsertStmt = db.compileStatement(
                    "INSERT OR REPLACE INTO $TABLE_SCHEDULES (channel_id, date, start_time, end_time, program_id, title, title_en, program_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                )
                for (s in itemsToUpsert) {
                    val chId = s.channelId ?: continue
                    val d = s.date ?: continue
                    val st = s.startTime ?: continue
                    val title = s.title ?: continue
                    val pid = s.programId ?: "prog_${title.hashCode()}"
                    affectedProgramIds.add(pid)

                    try {
                        upsertStmt.clearBindings()
                        upsertStmt.bindLong(1, chId)
                        upsertStmt.bindString(2, d)
                        upsertStmt.bindString(3, st)
                        if (s.endTime != null) upsertStmt.bindString(4, s.endTime) else upsertStmt.bindNull(4)
                        upsertStmt.bindString(5, pid)
                        upsertStmt.bindString(6, title)
                        if (s.title_en != null) upsertStmt.bindString(7, s.title_en) else upsertStmt.bindNull(7)
                        upsertStmt.bindString(8, s.programType ?: "movie")
                        upsertStmt.executeInsert()
                    } catch (e: Exception) {
                        android.util.Log.w("TvGuideDatabase", "Upsert error: ${e.message}")
                    }
                }
            }

            // 3. Incrementally update the derived shows table ONLY for affected programIds
            for (pid in affectedProgramIds) {
                updateDerivedShow(db, pid, channelsMap)
            }

            // 4. Update sync version
            val cv = ContentValues().apply {
                put("key", "version")
                put("value", delta.version.toString())
            }
            db.insertWithOnConflict(TABLE_SYNC_META, null, cv, SQLiteDatabase.CONFLICT_REPLACE)

            db.setTransactionSuccessful()
            return true
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "applyDelta failed: ${e.message}", e)
            return false
        } finally {
            db.endTransaction()
        }
    }

    private fun updateDerivedShow(db: SQLiteDatabase, programId: String, channelsMap: Map<Long, Channel>) {
        try {
            val c = db.rawQuery(
                "SELECT COUNT(*), MIN(date || ' ' || start_time), MIN(channel_id), title, title_en, program_type FROM $TABLE_SCHEDULES WHERE program_id = ? GROUP BY program_id",
                arrayOf(programId)
            )
            if (!c.moveToFirst() || c.getInt(0) == 0) {
                c.close()
                db.execSQL("DELETE FROM $TABLE_SHOWS WHERE program_id = ?", arrayOf(programId))
                return
            }

            val airingsCount = c.getInt(0)
            val firstDt = c.getString(1) ?: ""
            val sampleChId = c.getLong(2)
            val title = c.getString(3) ?: ""
            val titleEn = c.getString(4)
            val ptype = c.getString(5) ?: "movie"
            c.close()

            var poster: String? = null
            var overview: String? = null
            var rating: String? = "7.5"
            var priority = 4
            val progCur = db.rawQuery("SELECT poster, overview, rating, priority FROM $TABLE_PROGRAMS WHERE program_id = ? LIMIT 1", arrayOf(programId))
            if (progCur.moveToFirst()) {
                poster = progCur.getString(0)
                overview = progCur.getString(1)
                rating = progCur.getString(2) ?: "7.5"
                priority = progCur.getInt(3)
            } else {
                val classified = ContentClassifier.classify(title, titleEn, ptype, channelsMap[sampleChId]?.displayName)
                priority = CanonicalContentType.getPriority(classified.contentType)
            }
            progCur.close()

            val nearestDate = if (firstDt.length >= 10) firstDt.substring(0, 10) else ""
            val nearestTime = if (firstDt.length >= 16) firstDt.substring(11, 16) else ""
            val ch = channelsMap[sampleChId]
            if (poster.isNullOrBlank() || poster.startsWith("data:")) {
                poster = ch?.logoUrl
            }
            val nearestChannelName = ch?.displayName ?: ch?.nameAr ?: "قناة"
            val isPaidOnly = if (ch?.isPaidChannel == true) 1 else 0
            val hasFree = if (isPaidOnly == 1) 0 else 1

            val titleNorm = ArabicSearchHelper.normalizeArabic(title)
            val titleEnNorm = ArabicSearchHelper.normalizeArabic(titleEn)
            val chNorm = ArabicSearchHelper.normalizeArabic(nearestChannelName)

            val cv = ContentValues().apply {
                put("program_id", programId)
                put("title", title)
                put("title_en", titleEn)
                put("program_type", ptype)
                put("priority_tier", priority)
                put("poster", poster)
                put("overview", overview)
                put("rating", rating)
                put("airings_count", airingsCount)
                put("nearest_date", nearestDate)
                put("nearest_time", nearestTime)
                put("nearest_channel_name", nearestChannelName)
                put("nearest_channel_id", sampleChId)
                put("has_free_airings", hasFree)
                put("is_paid_only", isPaidOnly)
                put("title_norm", titleNorm)
                put("title_en_norm", titleEnNorm)
                put("channel_norm", chNorm)
            }
            db.insertWithOnConflict(TABLE_SHOWS, null, cv, SQLiteDatabase.CONFLICT_REPLACE)
        } catch (e: Exception) {
            android.util.Log.e("TvGuideDatabase", "updateDerivedShow error: ${e.message}", e)
        }
    }

    fun applyFullSnapshot(schedules: List<RawScheduleItem>, programs: Map<String, RawProgramItem>?, version: Int, channelsMap: Map<Long, Channel>) {
        val db = writableDatabase
        db.beginTransaction()
        try {
            db.execSQL("DELETE FROM $TABLE_SCHEDULES")
            if (programs != null && programs.isNotEmpty()) {
                db.execSQL("DELETE FROM $TABLE_PROGRAMS")
            }
            db.execSQL("DELETE FROM $TABLE_SHOWS")

            val sSql = "INSERT OR REPLACE INTO $TABLE_SCHEDULES (channel_id, date, start_time, end_time, program_id, title, title_en, program_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            val sStmt = db.compileStatement(sSql)
            for (s in schedules) {
                val chId = s.channelId ?: continue
                val d = s.date ?: continue
                val st = s.startTime ?: continue
                val title = s.title ?: continue
                val pid = s.programId ?: "prog_${title.hashCode()}"

                sStmt.clearBindings()
                sStmt.bindLong(1, chId)
                sStmt.bindString(2, d)
                sStmt.bindString(3, st)
                if (s.endTime != null) sStmt.bindString(4, s.endTime) else sStmt.bindNull(4)
                sStmt.bindString(5, pid)
                sStmt.bindString(6, title)
                if (s.title_en != null) sStmt.bindString(7, s.title_en) else sStmt.bindNull(7)
                sStmt.bindString(8, s.programType ?: "movie")
                sStmt.executeInsert()

                if (!s.poster.isNullOrBlank() && !s.poster.startsWith("data:")) {
                    val cvProg = ContentValues().apply {
                        put("program_id", pid)
                        put("title", title)
                        put("title_en", s.title_en)
                        put("program_type", s.programType ?: "movie")
                        put("priority", CanonicalContentType.getPriority(s.programType ?: "movie"))
                        put("poster", s.poster)
                        put("overview", s.overview)
                        put("rating", s.rating ?: "7.5")
                    }
                    db.insertWithOnConflict(TABLE_PROGRAMS, null, cvProg, SQLiteDatabase.CONFLICT_IGNORE)
                }
            }

            if (programs != null) {
                val pSql = "INSERT OR REPLACE INTO $TABLE_PROGRAMS (program_id, title, title_en, program_type, priority, poster, overview, rating, cast_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
                val pStmt = db.compileStatement(pSql)
                for ((k, p) in programs) {
                    val pid = p.programId ?: k
                    val title = p.title ?: k
                    pStmt.clearBindings()
                    pStmt.bindString(1, pid)
                    pStmt.bindString(2, title)
                    if (p.title_en != null) pStmt.bindString(3, p.title_en) else pStmt.bindNull(3)
                    pStmt.bindString(4, p.programType ?: "movie")
                    val priority = CanonicalContentType.getPriority(p.programType)
                    pStmt.bindLong(5, priority.toLong())
                    if (p.poster != null) pStmt.bindString(6, p.poster) else pStmt.bindNull(6)
                    if (p.overview != null) pStmt.bindString(7, p.overview) else pStmt.bindNull(7)
                    if (p.rating != null) pStmt.bindString(8, p.rating) else pStmt.bindNull(8)
                    val castJsonStr = if (p.cast.isNotEmpty()) json.encodeToString(p.cast) else null
                    if (castJsonStr != null) pStmt.bindString(9, castJsonStr) else pStmt.bindNull(9)
                    pStmt.executeInsert()
                }
            }

            val distinctPids = schedules.mapNotNull { it.programId }.distinct()
            for (pid in distinctPids) {
                updateDerivedShow(db, pid, channelsMap)
            }

            val cv = ContentValues().apply {
                put("key", "version")
                put("value", version.toString())
            }
            db.insertWithOnConflict(TABLE_SYNC_META, null, cv, SQLiteDatabase.CONFLICT_REPLACE)

            db.setTransactionSuccessful()
        } finally {
            db.endTransaction()
        }
    }
}
