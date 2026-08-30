package com.tvguide.app.data.models

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Frequency(
    val satellite: String? = "Nilesat 7.0°W",
    val frequency: String? = "11555",
    val polarization: String? = "V",
    @SerialName("symbol_rate") val symbolRate: String? = "27500",
    val fec: String? = "5/6",
    val quality: String? = "HD",
    val system: String? = "DVB-S2",
    @SerialName("is_encrypted") val isEncrypted: Boolean = false,
    val notes: String? = null
)

@Serializable
data class Channel(
    val id: Long = 0L,
    val name: String? = null,
    @SerialName("name_ar") val nameAr: String? = null,
    @SerialName("name_en") val nameEn: String? = null,
    @SerialName("logo_url") val logoUrl: String? = null,
    val source: String? = "rotana",
    @SerialName("source_channel_id") val sourceChannelId: String? = null,
    val country: String? = "EG",
    val language: String? = "ar",
    val category: String? = "general",
    val frequency: String? = null,
    val frequencies: List<Frequency> = emptyList(),
    @SerialName("elcinema_id") val elcinemaId: Long? = null,
    @SerialName("osn_guid") val osnGuid: String? = null,
    val quality: String? = "HD",
    @SerialName("is_paid") val isPaid: Boolean = false,
    @SerialName("is_encrypted") val isEncrypted: Boolean = false
) {
    val displayName: String get() = nameAr ?: name ?: nameEn ?: "قناة"
    val isPaidChannel: Boolean get() {
        if (isPaid || isEncrypted) return true
        val full = "${displayName} ${nameEn ?: ""} ${name ?: ""}".lowercase()
        return full.contains("osn") ||
               full.contains("أو إس إن") ||
               full.contains("او اس ان") ||
               full.contains("أوسن") ||
               full.contains("ياهلا") ||
               full.contains("يا هلا") ||
               full.contains("bein") ||
               full.contains("بي ان") ||
               full.contains("بي إن") ||
               full.contains("alfa") ||
               full.contains("ألفا") ||
               full.contains("الفا") ||
               full.contains("mbc+") ||
               full.contains("mbc +") ||
               full.contains("دراما +") ||
               full.contains("دراما+") ||
               full.contains("showcase") ||
               full.contains("mezze") ||
               full.contains("iqiyi")
    }
}

@Serializable
data class CastMember(
    val name: String = "",
    val character: String? = null,
    @SerialName("profile_path") val profilePath: String? = null
) {
    val profileUrl: String? get() = when {
        profilePath.isNullOrBlank() -> null
        profilePath.startsWith("http") -> profilePath
        else -> "https://image.tmdb.org/t/p/w185$profilePath"
    }
}

@Serializable
data class Airing(
    @SerialName("broadcast_id") val broadcastId: Long = 0L,
    @SerialName("channel_id") val channelId: Long = 0L,
    @SerialName("content_id") val contentId: Long = 0L,
    val title: String = "برنامج تلفزيوني",
    @SerialName("channel_name") val channelName: String = "",
    @SerialName("channel_logo") val channelLogo: String? = null,
    val poster: String? = null,
    val date: String = "",
    @SerialName("start_time") val startTime: String = "",
    @SerialName("end_time") val endTime: String? = null,
    @SerialName("start_datetime") val startDatetime: String = "",
    @SerialName("end_datetime") val endDatetime: String? = null
)

@Serializable
data class Content(
    val id: Long = 0L,
    @SerialName("title_ar") val titleAr: String = "",
    @SerialName("title_en") val titleEn: String? = null,
    @SerialName("original_title") val originalTitle: String? = null,
    @SerialName("content_type") val contentType: String = "movie",
    @SerialName("release_year") val releaseYear: Int? = 2024,
    val rating: String? = "7.8",
    @SerialName("poster_path") val posterPath: String? = null,
    @SerialName("backdrop_path") val backdropPath: String? = null,
    @SerialName("overview") val overview: String? = null,
    @SerialName("overview_ar") val overviewAr: String? = null,
    val genres: List<String> = emptyList(),
    val cast: List<CastMember> = emptyList(),
    @SerialName("runtime_minutes") val runtimeMinutes: Int? = null,
    @SerialName("tmdb_id") val tmdbId: Long? = null,
    @SerialName("airings_count") val airingsCount: Int = 0,
    val airings: List<Airing> = emptyList()
) {
    val posterUrl: String? get() = posterPath?.let { if (it.startsWith("http")) it else "https://image.tmdb.org/t/p/w500$it" }
    val backdropUrl: String? get() = backdropPath?.let { if (it.startsWith("http")) it else "https://image.tmdb.org/t/p/w780$it" }
    val displayOverview: String? get() = overviewAr ?: overview
}

@Serializable
data class NowAiringItem(
    @SerialName("broadcast_id") val broadcastId: Long = 0L,
    @SerialName("channel_id") val channelId: Long = 0L,
    @SerialName("channel_name") val channelName: String = "",
    @SerialName("channel_logo") val channelLogo: String? = null,
    @SerialName("content_id") val contentId: Long = 0L,
    val title: String = "",
    @SerialName("title_en") val titleEn: String? = null,
    @SerialName("content_type") val contentType: String = "movie",
    @SerialName("release_year") val releaseYear: Int? = 2024,
    val rating: String? = "7.5",
    @SerialName("poster_path") val posterPath: String? = null,
    @SerialName("backdrop_path") val backdropPath: String? = null,
    val overview: String? = null,
    @SerialName("start_time") val startTime: String = "",
    @SerialName("end_time") val endTime: String? = null,
    @SerialName("start_datetime") val startDatetime: String = "",
    @SerialName("end_datetime") val endDatetime: String? = null,
    @SerialName("remaining_minutes") val remainingMinutes: Int = 0,
    @SerialName("progress_percent") val progressPercent: Int = 0
) {
    val posterUrl: String? get() = posterPath?.let { if (it.startsWith("http")) it else "https://image.tmdb.org/t/p/w500$it" }
    val backdropUrl: String? get() = backdropPath?.let { if (it.startsWith("http")) it else "https://image.tmdb.org/t/p/w780$it" }
}

@Serializable
data class NextAiringItem(
    @SerialName("broadcast_id") val broadcastId: Long = 0L,
    @SerialName("channel_id") val channelId: Long = 0L,
    @SerialName("channel_name") val channelName: String = "",
    @SerialName("channel_logo") val channelLogo: String? = null,
    @SerialName("content_id") val contentId: Long = 0L,
    val title: String = "",
    @SerialName("title_en") val titleEn: String? = null,
    @SerialName("content_type") val contentType: String = "movie",
    @SerialName("release_year") val releaseYear: Int? = 2024,
    val rating: String? = "7.5",
    @SerialName("poster_path") val posterPath: String? = null,
    @SerialName("backdrop_path") val backdropPath: String? = null,
    val overview: String? = null,
    @SerialName("start_time") val startTime: String = "",
    @SerialName("end_time") val endTime: String? = null,
    @SerialName("start_datetime") val startDatetime: String = "",
    @SerialName("end_datetime") val endDatetime: String? = null
) {
    val posterUrl: String? get() = posterPath?.let { if (it.startsWith("http")) it else "https://image.tmdb.org/t/p/w500$it" }
}

@Serializable
data class SearchResults(
    val channels: List<Channel> = emptyList(),
    val shows: List<Content> = emptyList()
)
