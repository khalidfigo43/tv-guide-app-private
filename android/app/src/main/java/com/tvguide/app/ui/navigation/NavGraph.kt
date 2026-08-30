package com.tvguide.app.ui.navigation

import android.app.Activity
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.tvguide.app.data.models.*
import com.tvguide.app.ui.screens.*
import com.tvguide.app.ui.viewmodel.AppTab
import com.tvguide.app.util.AdMobHelper
import com.tvguide.app.util.AppCountryTimezone

@Composable
fun TVGuideNavHost(
    selectedTab: AppTab,
    onTabSelected: (AppTab) -> Unit,
    showPaidChannels: Boolean,
    onTogglePaidChannels: (Boolean) -> Unit,
    selectedTimezone: AppCountryTimezone,
    onTimezoneSelected: (AppCountryTimezone) -> Unit,
    nowAiring: List<NowAiringItem>,
    nextAiring: List<NextAiringItem>,
    movies: List<Content>,
    channels: List<Channel>,
    searchQuery: String,
    searchResults: SearchResults,
    isSearching: Boolean,
    onSearchQueryChange: (String) -> Unit,
    onClearSearch: () -> Unit,
    selectedShowCategory: String,
    onShowCategorySelected: (String) -> Unit,
    selectedChannelCategory: String,
    onChannelCategorySelected: (String) -> Unit,
    onGetMovieDetails: (Long) -> Content?,
    onGetChannelSchedule: (Long) -> List<Airing>,
    onGetChannelById: (Long) -> Channel?
) {
    val navController = rememberNavController()
    val context = LocalContext.current
    val activity = context as? Activity

    NavHost(
        navController = navController,
        startDestination = "home",
        modifier = Modifier.fillMaxSize()
    ) {
        composable("home") {
            HomeScreen(
                selectedTab = selectedTab,
                onTabSelected = onTabSelected,
                showPaidChannels = showPaidChannels,
                onTogglePaidChannels = onTogglePaidChannels,
                selectedTimezone = selectedTimezone,
                onTimezoneSelected = onTimezoneSelected,
                nowAiring = nowAiring,
                nextAiring = nextAiring,
                movies = movies,
                channels = channels,
                searchQuery = searchQuery,
                searchResults = searchResults,
                isSearching = isSearching,
                onSearchQueryChange = onSearchQueryChange,
                onClearSearch = onClearSearch,
                selectedShowCategory = selectedShowCategory,
                onShowCategorySelected = onShowCategorySelected,
                selectedChannelCategory = selectedChannelCategory,
                onChannelCategorySelected = onChannelCategorySelected,
                onMovieClick = { id ->
                    AdMobHelper.showInterstitialAdIfReady(activity) {
                        navController.navigate("movie/$id")
                    }
                },
                onChannelClick = { id ->
                    AdMobHelper.showInterstitialAdIfReady(activity) {
                        navController.navigate("channel/$id")
                    }
                }
            )
        }

        composable("movie/{id}") { backStackEntry ->
            val id = backStackEntry.arguments?.getString("id")?.toLongOrNull() ?: 1L
            val movie = onGetMovieDetails(id) ?: movies.firstOrNull { it.id == id }
            var isFav by remember { mutableStateOf(false) }

            if (movie != null) {
                MovieDetailScreen(
                    content = movie,
                    isFavorite = isFav,
                    onToggleFavorite = { isFav = !isFav },
                    onBackClick = { navController.popBackStack() },
                    onChannelClick = { chId -> navController.navigate("channel/$chId") }
                )
            }
        }

        composable("channel/{id}") { backStackEntry ->
            val id = backStackEntry.arguments?.getString("id")?.toLongOrNull() ?: 1L
            val channel = onGetChannelById(id) ?: channels.firstOrNull { it.id == id }
            val schedule = onGetChannelSchedule(id)

            if (channel != null) {
                ChannelDetailScreen(
                    channel = channel,
                    schedule = schedule,
                    onBackClick = { navController.popBackStack() },
                    onMovieClick = { movieId -> navController.navigate("movie/$movieId") }
                )
            }
        }
    }
}
