package com.tvguide.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.Coil
import coil.ImageLoader
import coil.disk.DiskCache
import coil.memory.MemoryCache
import com.tvguide.app.ui.navigation.TVGuideNavHost
import com.tvguide.app.ui.screens.SplashScreen
import com.tvguide.app.ui.theme.DarkBackground
import com.tvguide.app.ui.theme.TVGuideTheme
import com.tvguide.app.ui.viewmodel.TvGuideViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // Configure High Performance Coil Image Cache (Memory + 150MB Disk Cache)
        val imageLoader = ImageLoader.Builder(this)
            .memoryCache {
                MemoryCache.Builder(this)
                    .maxSizePercent(0.25)
                    .build()
            }
            .diskCache {
                DiskCache.Builder()
                    .directory(cacheDir.resolve("image_cache"))
                    .maxSizeBytes(150L * 1024 * 1024)
                    .build()
            }
            .crossfade(true)
            .respectCacheHeaders(false)
            .build()
        Coil.setImageLoader(imageLoader)

        setContent {
            TVGuideTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = DarkBackground
                ) {
                    val viewModel: TvGuideViewModel = viewModel()
                    val uiState by viewModel.uiState.collectAsState()

                    if (uiState.isLoading) {
                        SplashScreen()
                    } else {
                        TVGuideNavHost(
                            selectedTab = uiState.selectedTab,
                            onTabSelected = { tab -> viewModel.selectTab(tab) },
                            showPaidChannels = uiState.showPaidChannels,
                            onTogglePaidChannels = { show -> viewModel.togglePaidChannels(show) },
                            selectedTimezone = uiState.selectedTimezone,
                            onTimezoneSelected = { tz -> viewModel.setTimezone(tz) },
                            nowAiring = uiState.nowAiring,
                            nextAiring = uiState.nextAiring,
                            movies = uiState.movies,
                            channels = uiState.channels,
                            searchQuery = uiState.searchQuery,
                            searchResults = uiState.searchResults,
                            isSearching = uiState.isSearching,
                            onSearchQueryChange = { q -> viewModel.search(q) },
                            onClearSearch = { viewModel.clearSearch() },
                            selectedShowCategory = uiState.selectedShowCategory,
                            onShowCategorySelected = { cat -> viewModel.setShowCategory(cat) },
                            selectedChannelCategory = uiState.selectedChannelCategory,
                            onChannelCategorySelected = { cat -> viewModel.setChannelCategory(cat) },
                            onGetMovieDetails = { id -> viewModel.getMovieDetails(id) },
                            onGetChannelSchedule = { id -> viewModel.getChannelSchedule(id) },
                            onGetChannelById = { id -> viewModel.getChannelById(id) }
                        )
                    }
                }
            }
        }
    }
}
