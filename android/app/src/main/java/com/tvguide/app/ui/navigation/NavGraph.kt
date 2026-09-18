package com.tvguide.app.ui.navigation

import android.app.Activity
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.tvguide.app.data.models.*
import com.tvguide.app.ui.screens.*
import com.tvguide.app.ui.theme.DarkBackground
import com.tvguide.app.ui.theme.PrimaryRed
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
    rawAllChannels: List<Channel> = emptyList(),
    searchQuery: String,
    searchResults: SearchResults,
    isSearching: Boolean,
    isRefreshing: Boolean = false,
    onRefreshClick: () -> Unit = {},
    onSearchQueryChange: (String) -> Unit,
    onClearSearch: () -> Unit,
    selectedShowCategory: String,
    onShowCategorySelected: (String) -> Unit,
    selectedChannelCategory: String,
    onChannelCategorySelected: (String) -> Unit,
    categoryOrder: List<String> = emptyList(),
    onCategoryOrderChange: (List<String>) -> Unit = {},
    favoriteChannelIds: List<Long> = emptyList(),
    onToggleFavorite: (Long) -> Unit = {},
    onMoveFavorite: (Int, Int) -> Unit = { _, _ -> },
    hiddenChannelIds: Set<Long> = emptySet(),
    onToggleHideChannel: (Long) -> Unit = {},
    onUnhideAllChannels: () -> Unit = {},
    onGetMovieDetails: (Long) -> Content?,
    onGetChannelSchedule: (Long) -> List<Airing>,
    onGetChannelById: (Long) -> Channel?,
    onUpdateShowCategory: (Long, String, String) -> Unit = { _, _, _ -> },
    onHideShow: (String) -> Unit = {}
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
                rawAllChannels = rawAllChannels,
                searchQuery = searchQuery,
                searchResults = searchResults,
                isSearching = isSearching,
                isRefreshing = isRefreshing,
                onRefreshClick = onRefreshClick,
                onSearchQueryChange = onSearchQueryChange,
                onClearSearch = onClearSearch,
                selectedShowCategory = selectedShowCategory,
                onShowCategorySelected = onShowCategorySelected,
                selectedChannelCategory = selectedChannelCategory,
                onChannelCategorySelected = onChannelCategorySelected,
                categoryOrder = categoryOrder,
                onCategoryOrderChange = onCategoryOrderChange,
                favoriteChannelIds = favoriteChannelIds,
                onToggleFavorite = onToggleFavorite,
                onMoveFavorite = onMoveFavorite,
                hiddenChannelIds = hiddenChannelIds,
                onToggleHideChannel = onToggleHideChannel,
                onUnhideAllChannels = onUnhideAllChannels,
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
                    onChannelClick = { chId -> navController.navigate("channel/$chId") },
                    onUpdateCategory = { newCat -> onUpdateShowCategory(id, movie.titleAr, newCat) },
                    onHideShow = { title -> onHideShow(title) }
                )
            } else {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(DarkBackground),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        modifier = Modifier.padding(24.dp)
                    ) {
                        Text(
                            text = "عذراً، لم نتمكن من العثور على تفاصيل هذا العرض",
                            color = Color.White,
                            style = MaterialTheme.typography.bodyLarge
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(
                            onClick = { navController.popBackStack() },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = PrimaryRed
                            )
                        ) {
                            Text("رجوع", color = Color.White)
                        }
                    }
                }
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
