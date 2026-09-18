package com.tvguide.app

import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Surface
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.viewmodel.compose.viewModel
import coil.Coil
import coil.ImageLoader
import coil.disk.DiskCache
import coil.memory.MemoryCache
import com.tvguide.app.ui.components.UpdateDialog
import com.tvguide.app.ui.navigation.TVGuideNavHost
import com.tvguide.app.ui.screens.SplashScreen
import com.tvguide.app.ui.theme.DarkBackground
import com.tvguide.app.ui.theme.TVGuideTheme
import com.tvguide.app.ui.viewmodel.TvGuideViewModel
import com.tvguide.app.util.AdMobHelper
import com.tvguide.app.util.AppUpdateInfo
import com.tvguide.app.util.UpdateManager
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        // 1. Initialize Google AdMob
        AdMobHelper.initialize(this)

        // 2. Configure High Performance Coil Image Cache (Memory + 150MB Disk Cache)
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
                    val context = LocalContext.current
                    val scope = rememberCoroutineScope()
                    val viewModel: TvGuideViewModel = viewModel()
                    val uiState by viewModel.uiState.collectAsState()

                    // Onboarding State
                    var showOnboarding by remember {
                        mutableStateOf(!com.tvguide.app.ui.screens.OnboardingPrefs.isOnboardingCompleted(context))
                    }

                    // Auto-Update State
                    var availableUpdate by remember { mutableStateOf<AppUpdateInfo?>(null) }
                    var isDownloadingUpdate by remember { mutableStateOf(false) }
                    var downloadProgress by remember { mutableStateOf(0f) }

                    // Check for Updates on App Start
                    LaunchedEffect(Unit) {
                        try {
                            val currentVersionCode = try {
                                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                                    packageManager.getPackageInfo(packageName, PackageManager.PackageInfoFlags.of(0)).longVersionCode.toInt()
                                } else {
                                    @Suppress("DEPRECATION")
                                    packageManager.getPackageInfo(packageName, 0).versionCode
                                }
                            } catch (e: Exception) {
                                BuildConfig.VERSION_CODE
                            }
                            val update = UpdateManager.checkForUpdate(currentVersionCode)
                            if (update != null) {
                                availableUpdate = update
                            }
                        } catch (e: Exception) {
                            e.printStackTrace()
                        }
                    }

                    if (uiState.isLoading) {
                        SplashScreen()
                    } else if (showOnboarding) {
                        com.tvguide.app.ui.screens.OnboardingScreen(
                            onFinished = { showOnboarding = false }
                        )
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
                            rawAllChannels = uiState.rawAllChannels,
                            searchQuery = uiState.searchQuery,
                            searchResults = uiState.searchResults,
                            isSearching = uiState.isSearching,
                            isRefreshing = uiState.isRefreshing,
                            onRefreshClick = {
                                Toast.makeText(context, "جاري فحص وتحديث جداول العروض...", Toast.LENGTH_SHORT).show()
                                viewModel.refreshSchedules { updated ->
                                    Toast.makeText(
                                        context,
                                        if (updated) "تم تحديث جداول العروض بنجاح 🔄" else "جداول العروض محدثة بالفعل ✅",
                                        Toast.LENGTH_SHORT
                                    ).show()
                                }
                            },
                            onSearchQueryChange = { q -> viewModel.search(q) },
                            onClearSearch = { viewModel.clearSearch() },
                            selectedShowCategory = uiState.selectedShowCategory,
                            onShowCategorySelected = { cat -> viewModel.setShowCategory(cat) },
                            selectedChannelCategory = uiState.selectedChannelCategory,
                            onChannelCategorySelected = { cat -> viewModel.setChannelCategory(cat) },
                            categoryOrder = uiState.categoryOrder,
                            onCategoryOrderChange = { order -> viewModel.setCategoryOrder(order) },
                            favoriteChannelIds = uiState.favoriteChannelIds,
                            onToggleFavorite = { id -> viewModel.toggleFavoriteChannel(id) },
                            onMoveFavorite = { from, to -> viewModel.moveFavoriteChannel(from, to) },
                            hiddenChannelIds = uiState.hiddenChannelIds,
                            onToggleHideChannel = { id -> viewModel.toggleHideChannel(id) },
                            onUnhideAllChannels = { viewModel.unhideAllChannels() },
                            onGetMovieDetails = { id -> viewModel.getMovieDetails(id) },
                            onGetChannelSchedule = { id -> viewModel.getChannelSchedule(id) },
                            onGetChannelById = { id -> viewModel.getChannelById(id) },
                            onUpdateShowCategory = { id, title, cat -> viewModel.updateShowCategory(id, title, cat) },
                            onHideShow = { title -> viewModel.hideShow(title) }
                        )
                    }

                    // In-App Auto Update Dialog
                    availableUpdate?.let { updateInfo ->
                        UpdateDialog(
                            updateInfo = updateInfo,
                            isDownloading = isDownloadingUpdate,
                            downloadProgress = downloadProgress,
                            onStartDownload = {
                                isDownloadingUpdate = true
                                downloadProgress = 0f
                                scope.launch {
                                    UpdateManager.downloadAndInstallApk(
                                        context = context,
                                        apkUrl = updateInfo.apkUrl,
                                        versionName = updateInfo.versionName,
                                        onProgress = { p -> downloadProgress = p },
                                        onComplete = {
                                            isDownloadingUpdate = false
                                            availableUpdate = null
                                        },
                                        onError = { err ->
                                            isDownloadingUpdate = false
                                            Toast.makeText(context, err, Toast.LENGTH_LONG).show()
                                        }
                                    )
                                }
                            },
                            onDismiss = {
                                availableUpdate = null
                            }
                        )
                    }
                }
            }
        }
    }
}
