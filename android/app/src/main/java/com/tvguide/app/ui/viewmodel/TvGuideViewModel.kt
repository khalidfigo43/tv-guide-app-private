package com.tvguide.app.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.tvguide.app.data.models.*
import com.tvguide.app.data.repository.TvGuideRepository
import com.tvguide.app.util.AppCountryTimezone
import com.tvguide.app.util.TimezoneHelper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

enum class AppTab {
    LIVE_NOW,
    UP_NEXT,
    ALL_SHOWS,
    CHANNELS
}

data class TvGuideUiState(
    val isLoading: Boolean = true,
    val isRefreshing: Boolean = false,
    val selectedTab: AppTab = AppTab.LIVE_NOW,
    val showPaidChannels: Boolean = false,
    val selectedTimezone: AppCountryTimezone = TimezoneHelper.detectDefaultCountry(),
    val nowAiring: List<NowAiringItem> = emptyList(),
    val nextAiring: List<NextAiringItem> = emptyList(),
    val movies: List<Content> = emptyList(),
    val channels: List<Channel> = emptyList(),
    val searchQuery: String = "",
    val searchResults: SearchResults = SearchResults(),
    val isSearching: Boolean = false,
    val selectedShowCategory: String = "all",
    val selectedChannelCategory: String = "all",
    val errorMessage: String? = null
)

class TvGuideViewModel(application: Application) : AndroidViewModel(application) {

    private val repository = TvGuideRepository(context = application.applicationContext)
    private val _uiState = MutableStateFlow(TvGuideUiState())
    val uiState: StateFlow<TvGuideUiState> = _uiState.asStateFlow()

    private var searchJob: Job? = null

    private val t0ProcessStart = System.currentTimeMillis()

    init {
        val t1Created = System.currentTimeMillis()
        android.util.Log.i("TvGuideStartup", "T0->T1: ViewModel created in ${t1Created - t0ProcessStart}ms")

        // 1. Instant local load (T2 -> T3 -> T4)
        loadData()

        // 2. Safe background sync - starts after 8 seconds so UI is completely rendered
        viewModelScope.launch(Dispatchers.IO) {
            try {
                delay(8000)
                val t5SyncStart = System.currentTimeMillis()
                android.util.Log.i("TvGuideStartup", "T5: Background sync started at +${t5SyncStart - t0ProcessStart}ms from launch")
                val updated = repository.syncLatestSchedulesOnline(force = false)
                val t6SyncEnd = System.currentTimeMillis()
                android.util.Log.i("TvGuideStartup", "T6: Background sync finished in ${t6SyncEnd - t5SyncStart}ms (updated=$updated)")
                if (updated) {
                    loadData()
                }
            } catch (e: Throwable) {
                android.util.Log.w("TvGuideStartup", "Background sync completed safely: ${e.message}")
            }
        }
    }

    private fun getCurrentOffset(): Int {
        return TimezoneHelper.getEffectiveOffset(_uiState.value.selectedTimezone)
    }

    fun loadData() {
        viewModelScope.launch {
            val includePaid = _uiState.value.showPaidChannels
            val offset = getCurrentOffset()

            val t2DbStart = System.currentTimeMillis()
            android.util.Log.i("TvGuideStartup", "T2: Local database read started at +${t2DbStart - t0ProcessStart}ms")

            // 1. Always load Channels independently so channels tab is NEVER empty
            try {
                val channelsRes = repository.getChannels(
                    category = _uiState.value.selectedChannelCategory,
                    includePaid = includePaid
                )
                _uiState.value = _uiState.value.copy(
                    channels = channelsRes.getOrDefault(emptyList())
                )
            } catch (e: Throwable) {
                android.util.Log.e("TvGuideStartup", "Channels load error: ${e.message}", e)
            }

            // 2. Load Now Airing and unblock UI immediately
            try {
                val nowRes = repository.getNowAiring(includePaid = includePaid, timezoneOffset = offset)
                val t3DataReady = System.currentTimeMillis()
                android.util.Log.i("TvGuideStartup", "T3: First local data ready in ${t3DataReady - t2DbStart}ms (total from launch: ${t3DataReady - t0ProcessStart}ms)")

                _uiState.value = _uiState.value.copy(
                    isLoading = false,
                    nowAiring = nowRes.getOrDefault(emptyList())
                )

                val t4Rendered = System.currentTimeMillis()
                android.util.Log.i("TvGuideStartup", "T4: Main UI rendered with local data at +${t4Rendered - t0ProcessStart}ms from launch")
            } catch (e: Throwable) {
                android.util.Log.e("TvGuideStartup", "Now airing load error: ${e.message}", e)
                _uiState.value = _uiState.value.copy(isLoading = false)
            }

            // 3. Concurrently populate Next Airing and Shows/Movies
            try {
                val nextRes = repository.getNextAiring(includePaid = includePaid, timezoneOffset = offset)
                val moviesRes = repository.getMovies(
                    category = _uiState.value.selectedShowCategory,
                    includePaid = includePaid,
                    timezoneOffset = offset
                )

                _uiState.value = _uiState.value.copy(
                    nextAiring = nextRes.getOrDefault(emptyList()),
                    movies = moviesRes.getOrDefault(emptyList())
                )
            } catch (e: Throwable) {
                android.util.Log.e("TvGuideStartup", "Next/movies load error: ${e.message}", e)
            }
        }
    }

    fun refreshSchedules(onComplete: (Boolean) -> Unit = {}) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isRefreshing = true)
            try {
                val updated = repository.syncLatestSchedulesOnline(force = true)
                loadData()
                _uiState.value = _uiState.value.copy(isRefreshing = false)
                onComplete(updated)
            } catch (e: Throwable) {
                _uiState.value = _uiState.value.copy(isRefreshing = false)
                onComplete(false)
            }
        }
    }

    fun setTimezone(timezone: AppCountryTimezone) {
        _uiState.value = _uiState.value.copy(selectedTimezone = timezone)
        loadData()
        if (_uiState.value.searchQuery.isNotBlank()) {
            search(_uiState.value.searchQuery)
        }
    }

    fun togglePaidChannels(show: Boolean) {
        _uiState.value = _uiState.value.copy(showPaidChannels = show)
        loadData()
        if (_uiState.value.searchQuery.isNotBlank()) {
            search(_uiState.value.searchQuery)
        }
    }

    fun selectTab(tab: AppTab) {
        _uiState.value = _uiState.value.copy(selectedTab = tab)
    }

    fun setShowCategory(category: String) {
        _uiState.value = _uiState.value.copy(selectedShowCategory = category)
        viewModelScope.launch {
            try {
                val res = repository.getMovies(
                    category = category,
                    includePaid = _uiState.value.showPaidChannels,
                    timezoneOffset = getCurrentOffset()
                )
                _uiState.value = _uiState.value.copy(movies = res.getOrDefault(emptyList()))
            } catch (e: Throwable) {
                android.util.Log.e("TvGuideViewModel", "setShowCategory error: ${e.message}", e)
            }
        }
    }

    fun setChannelCategory(category: String) {
        _uiState.value = _uiState.value.copy(selectedChannelCategory = category)
        viewModelScope.launch {
            try {
                val res = repository.getChannels(
                    category = category,
                    includePaid = _uiState.value.showPaidChannels
                )
                _uiState.value = _uiState.value.copy(channels = res.getOrDefault(emptyList()))
            } catch (e: Throwable) {
                android.util.Log.e("TvGuideViewModel", "setChannelCategory error: ${e.message}", e)
            }
        }
    }

    fun search(query: String) {
        _uiState.value = _uiState.value.copy(searchQuery = query)
        searchJob?.cancel()
        if (query.isBlank()) {
            _uiState.value = _uiState.value.copy(searchResults = SearchResults(), isSearching = false)
            return
        }
        searchJob = viewModelScope.launch {
            delay(120) // Debounce typing by 120ms
            _uiState.value = _uiState.value.copy(isSearching = true)
            try {
                val res = repository.searchAll(
                    query = query,
                    includePaid = _uiState.value.showPaidChannels,
                    timezoneOffset = getCurrentOffset()
                )
                _uiState.value = _uiState.value.copy(
                    searchResults = res.getOrDefault(SearchResults()),
                    isSearching = false
                )
            } catch (e: Throwable) {
                android.util.Log.e("TvGuideSearch", "Search error: ${e.message}", e)
                _uiState.value = _uiState.value.copy(isSearching = false)
            }
        }
    }

    fun clearSearch() {
        searchJob?.cancel()
        _uiState.value = _uiState.value.copy(searchQuery = "", searchResults = SearchResults(), isSearching = false)
    }

    fun getMovieDetails(id: Long): Content? {
        return repository.getContentDetailsSync(id, getCurrentOffset())
            ?: _uiState.value.movies.firstOrNull { it.id == id }
            ?: _uiState.value.searchResults.shows.firstOrNull { it.id == id }
    }

    fun getChannelById(id: Long): Channel? {
        return _uiState.value.channels.firstOrNull { it.id == id }
    }

    fun getChannelSchedule(channelId: Long): List<Airing> {
        return repository.getChannelScheduleSync(channelId, getCurrentOffset())
    }

    fun updateShowCategory(showId: Long?, title: String?, newCategory: String) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.updateShowCategory(showId, title, newCategory)
            loadData()
        }
    }

    fun hideShow(title: String) {
        viewModelScope.launch(Dispatchers.IO) {
            repository.hideShow(title)
            loadData()
        }
    }
}
