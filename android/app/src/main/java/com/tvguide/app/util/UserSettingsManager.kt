package com.tvguide.app.util

import android.content.Context
import android.content.SharedPreferences
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

class UserSettingsManager(context: Context) {

    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val json = Json { ignoreUnknownKeys = true }

    companion object {
        private const val PREFS_NAME = "tvguide_user_settings"
        private const val KEY_CATEGORY_ORDER = "key_category_order"
        private const val KEY_FAVORITE_CHANNELS = "key_favorite_channels"
        private const val KEY_HIDDEN_CHANNELS = "key_hidden_channels"

        val DEFAULT_CATEGORY_ORDER = listOf("movie", "series", "cartoon", "other")
    }

    // ---------------------------------------------------------------------------------------------
    // 1. CATEGORY PRIORITY ORDER
    // ---------------------------------------------------------------------------------------------

    fun getCategoryOrder(): List<String> {
        val storedJson = prefs.getString(KEY_CATEGORY_ORDER, null) ?: return DEFAULT_CATEGORY_ORDER
        return try {
            val list = json.decodeFromString<List<String>>(storedJson)
            if (list.isNotEmpty()) list else DEFAULT_CATEGORY_ORDER
        } catch (e: Exception) {
            DEFAULT_CATEGORY_ORDER
        }
    }

    fun setCategoryOrder(order: List<String>) {
        try {
            val encoded = json.encodeToString(order)
            prefs.edit().putString(KEY_CATEGORY_ORDER, encoded).apply()
        } catch (e: Exception) {
            android.util.Log.e("UserSettingsManager", "Error saving category order: ${e.message}")
        }
    }

    fun getPriorityForCategory(category: String): Int {
        val normalized = when (category.lowercase().trim()) {
            "movie", "film", "movies", "أفلام", "فيلم" -> "movie"
            "series", "drama", "مسلسلات", "مسلسل" -> "series"
            "cartoon", "kids", "animation", "كارتون", "أطفال" -> "cartoon"
            else -> "other"
        }
        val order = getCategoryOrder()
        val index = order.indexOf(normalized)
        return if (index != -1) index + 1 else 4
    }

    // ---------------------------------------------------------------------------------------------
    // 2. FAVORITE CHANNELS (ORDERED LIST)
    // ---------------------------------------------------------------------------------------------

    fun getFavoriteChannels(): List<Long> {
        val storedJson = prefs.getString(KEY_FAVORITE_CHANNELS, null) ?: return emptyList()
        return try {
            json.decodeFromString<List<Long>>(storedJson)
        } catch (e: Exception) {
            emptyList()
        }
    }

    fun setFavoriteChannels(channels: List<Long>) {
        try {
            val encoded = json.encodeToString(channels)
            prefs.edit().putString(KEY_FAVORITE_CHANNELS, encoded).apply()
        } catch (e: Exception) {
            android.util.Log.e("UserSettingsManager", "Error saving favorite channels: ${e.message}")
        }
    }

    fun isFavoriteChannel(channelId: Long): Boolean {
        return getFavoriteChannels().contains(channelId)
    }

    fun toggleFavoriteChannel(channelId: Long): Boolean {
        val current = getFavoriteChannels().toMutableList()
        val isNowFav = if (current.contains(channelId)) {
            current.remove(channelId)
            false
        } else {
            current.add(channelId)
            true
        }
        setFavoriteChannels(current)
        return isNowFav
    }

    fun moveFavoriteChannel(fromIndex: Int, toIndex: Int) {
        val current = getFavoriteChannels().toMutableList()
        if (fromIndex in current.indices && toIndex in current.indices) {
            val item = current.removeAt(fromIndex)
            current.add(toIndex, item)
            setFavoriteChannels(current)
        }
    }

    // ---------------------------------------------------------------------------------------------
    // 3. HIDDEN / BLOCKED CHANNELS
    // ---------------------------------------------------------------------------------------------

    fun getHiddenChannels(): Set<Long> {
        val storedJson = prefs.getString(KEY_HIDDEN_CHANNELS, null) ?: return emptySet()
        return try {
            json.decodeFromString<Set<Long>>(storedJson)
        } catch (e: Exception) {
            emptySet()
        }
    }

    fun setHiddenChannels(channels: Set<Long>) {
        try {
            val encoded = json.encodeToString(channels)
            prefs.edit().putString(KEY_HIDDEN_CHANNELS, encoded).apply()
        } catch (e: Exception) {
            android.util.Log.e("UserSettingsManager", "Error saving hidden channels: ${e.message}")
        }
    }

    fun isChannelHidden(channelId: Long): Boolean {
        return getHiddenChannels().contains(channelId)
    }

    fun toggleHideChannel(channelId: Long): Boolean {
        val current = getHiddenChannels().toMutableSet()
        val isNowHidden = if (current.contains(channelId)) {
            current.remove(channelId)
            false
        } else {
            // Also remove from favorites if hiding
            val favs = getFavoriteChannels().toMutableList()
            if (favs.contains(channelId)) {
                favs.remove(channelId)
                setFavoriteChannels(favs)
            }
            current.add(channelId)
            true
        }
        setHiddenChannels(current)
        return isNowHidden
    }

    fun unhideAllChannels() {
        setHiddenChannels(emptySet())
    }
}

