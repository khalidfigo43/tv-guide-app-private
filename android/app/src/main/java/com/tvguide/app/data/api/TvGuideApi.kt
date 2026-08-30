package com.tvguide.app.data.api

import com.tvguide.app.data.models.*
import kotlinx.serialization.json.Json
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import retrofit2.http.GET
import retrofit2.http.Path
import retrofit2.http.Query
import java.util.concurrent.TimeUnit

interface TvGuideApi {

    @GET("api/channels")
    suspend fun getChannels(): List<Channel>

    @GET("api/now")
    suspend fun getNowAiring(): List<NowAiringItem>

    @GET("api/next")
    suspend fun getNextAiring(): List<NextAiringItem>

    @GET("api/movies")
    suspend fun getMovies(
        @Query("type") type: String? = null,
        @Query("genre") genre: String? = null,
        @Query("search") search: String? = null,
        @Query("page") page: Int = 1,
        @Query("limit") limit: Int = 50
    ): Map<String, kotlinx.serialization.json.JsonElement>

    @GET("api/content/{id}")
    suspend fun getContentDetails(@Path("id") id: Long): Content

    @GET("api/channels/{channel_id}/schedule")
    suspend fun getChannelSchedule(
        @Path("channel_id") channelId: Long,
        @Query("date") date: String? = null
    ): List<Airing>

    @GET("api/search")
    suspend fun search(@Query("q") query: String): List<Content>

    companion object {
        // Default local development base URL (10.0.2.2 is the host machine when running in Android Emulator)
        // or replace with your production server IP/Domain
        var BASE_URL = "http://10.0.2.2:8000/"

        fun create(baseUrl: String = BASE_URL): TvGuideApi {
            val json = Json {
                ignoreUnknownKeys = true
                coerceInputValues = true
                isLenient = true
            }

            val logging = HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            }

            val client = OkHttpClient.Builder()
                .addInterceptor(logging)
                .connectTimeout(20, TimeUnit.SECONDS)
                .readTimeout(20, TimeUnit.SECONDS)
                .build()

            return Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(client)
                .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
                .build()
                .create(TvGuideApi::class.java)
        }
    }
}

