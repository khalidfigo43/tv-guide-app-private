package com.tvguide.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.GridItemSpan
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.tvguide.app.data.models.*
import com.tvguide.app.ui.components.BannerAdView
import com.tvguide.app.ui.theme.*
import com.tvguide.app.ui.viewmodel.AppTab
import com.tvguide.app.util.AppCountryTimezone
import com.tvguide.app.util.TimezoneHelper

@Composable
fun HomeScreen(
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
    onMovieClick: (Long) -> Unit,
    onChannelClick: (Long) -> Unit
) {
    var showTimezoneDialog by remember { mutableStateOf(false) }

    Scaffold(
        topBar = {
            TopSearchBar(
                query = searchQuery,
                onQueryChange = onSearchQueryChange,
                onClear = onClearSearch,
                selectedTimezone = selectedTimezone,
                onTimezoneClick = { showTimezoneDialog = true }
            )
        },
        bottomBar = {
            Column(modifier = Modifier.fillMaxWidth().navigationBarsPadding()) {
                BannerAdView()
                BottomNavBar(
                    selectedTab = selectedTab,
                    onTabSelected = {
                        onClearSearch()
                        onTabSelected(it)
                    }
                )
            }
        },
        containerColor = DarkBackground
    ) { paddingValues ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .background(DarkBackground)
        ) {
            if (searchQuery.isNotBlank()) {
                // Search Results Screen (3 Cards Per Row Grid)
                SearchResultsView(
                    query = searchQuery,
                    searchResults = searchResults,
                    onMovieClick = onMovieClick,
                    onChannelClick = onChannelClick
                )
            } else {
                // Tab Content (3 Cards Per Row Grid)
                when (selectedTab) {
                    AppTab.LIVE_NOW -> LiveNowTabView(
                        items = nowAiring,
                        onItemClick = onMovieClick,
                        onChannelClick = onChannelClick
                    )
                    AppTab.UP_NEXT -> UpNextTabView(
                        items = nextAiring,
                        onItemClick = onMovieClick,
                        onChannelClick = onChannelClick
                    )
                    AppTab.ALL_SHOWS -> AllShowsTabView(
                        movies = movies,
                        selectedCategory = selectedShowCategory,
                        onCategorySelected = onShowCategorySelected,
                        onMovieClick = onMovieClick
                    )
                    AppTab.CHANNELS -> ChannelsTabView(
                        channels = channels,
                        selectedCategory = selectedChannelCategory,
                        showPaidChannels = showPaidChannels,
                        onTogglePaidChannels = onTogglePaidChannels,
                        onCategorySelected = onChannelCategorySelected,
                        onChannelClick = onChannelClick
                    )
                }
            }

            // Country / Timezone Picker Dialog
            if (showTimezoneDialog) {
                TimezonePickerDialog(
                    currentTimezone = selectedTimezone,
                    onTimezoneSelected = {
                        onTimezoneSelected(it)
                        showTimezoneDialog = false
                    },
                    onDismiss = { showTimezoneDialog = false }
                )
            }
        }
    }
}

@Composable
fun TopSearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    onClear: () -> Unit,
    selectedTimezone: AppCountryTimezone,
    onTimezoneClick: () -> Unit
) {
    Surface(
        color = DarkSurface,
        modifier = Modifier
            .fillMaxWidth()
            .statusBarsPadding()
            .padding(horizontal = 10.dp, vertical = 2.dp),
        shape = RoundedCornerShape(12.dp),
        shadowElevation = 2.dp
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .height(40.dp)
                .padding(horizontal = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Icon(
                imageVector = Icons.Default.Search,
                contentDescription = "Search",
                tint = AccentGold,
                modifier = Modifier.size(18.dp)
            )
            Spacer(modifier = Modifier.width(6.dp))

            Box(
                modifier = Modifier.weight(1f),
                contentAlignment = Alignment.CenterStart
            ) {
                if (query.isEmpty()) {
                    Text(
                        text = "ابحث عن فيلم، مسلسل، قناة، ممثل...",
                        color = TextSecondary,
                        fontSize = 12.sp,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
                androidx.compose.foundation.text.BasicTextField(
                    value = query,
                    onValueChange = onQueryChange,
                    singleLine = true,
                    maxLines = 1,
                    textStyle = androidx.compose.ui.text.TextStyle(
                        color = Color.White,
                        fontSize = 13.sp,
                        fontWeight = FontWeight.Medium
                    ),
                    cursorBrush = androidx.compose.ui.graphics.SolidColor(PrimaryRed),
                    keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
                    modifier = Modifier.fillMaxWidth()
                )
            }

            if (query.isNotBlank()) {
                IconButton(
                    onClick = onClear,
                    modifier = Modifier.size(24.dp)
                ) {
                    Icon(
                        imageVector = Icons.Default.Close,
                        contentDescription = "Clear",
                        tint = TextSecondary,
                        modifier = Modifier.size(16.dp)
                    )
                }
                Spacer(modifier = Modifier.width(4.dp))
            }

            // Country & Timezone Button
            Surface(
                color = DarkSurfaceVariant,
                shape = RoundedCornerShape(8.dp),
                modifier = Modifier
                    .height(28.dp)
                    .clickable(onClick = onTimezoneClick)
            ) {
                Row(
                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = selectedTimezone.flag,
                        fontSize = 12.sp
                    )
                    Spacer(modifier = Modifier.width(3.dp))
                    Icon(
                        imageVector = Icons.Default.Public,
                        contentDescription = "Timezone",
                        tint = AccentCyan,
                        modifier = Modifier.size(12.dp)
                    )
                }
            }
        }
    }
}

@Composable
fun TimezonePickerDialog(
    currentTimezone: AppCountryTimezone,
    onTimezoneSelected: (AppCountryTimezone) -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = DarkSurface,
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.Public, contentDescription = null, tint = AccentGold)
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "تحديد الدولة وضبط التوقيت 🌍",
                    color = Color.White,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text(
                    text = "اختر دولتك لضبط مواعيد عرض البرامج تلقائياً حسب توقيتك المحلي:",
                    color = TextSecondary,
                    fontSize = 12.sp
                )
                Spacer(modifier = Modifier.height(4.dp))
                LazyColumn(
                    modifier = Modifier
                        .fillMaxWidth()
                        .heightIn(max = 380.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(TimezoneHelper.supportedCountries) { country ->
                        val isSelected = country.id == currentTimezone.id
                        Surface(
                            color = if (isSelected) AccentCyan.copy(alpha = 0.15f) else DarkSurfaceVariant,
                            shape = RoundedCornerShape(10.dp),
                            modifier = Modifier
                                .fillMaxWidth()
                                .border(
                                    width = if (isSelected) 1.5.dp else 0.dp,
                                    color = if (isSelected) AccentCyan else Color.Transparent,
                                    shape = RoundedCornerShape(10.dp)
                                )
                                .clickable { onTimezoneSelected(country) }
                        ) {
                            Row(
                                modifier = Modifier.padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    modifier = Modifier.weight(1f)
                                ) {
                                    Text(text = country.flag, fontSize = 18.sp)
                                    Spacer(modifier = Modifier.width(10.dp))
                                    Text(
                                        text = country.countryNameAr,
                                        color = if (isSelected) Color.White else TextSecondary,
                                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                        fontSize = 13.sp
                                    )
                                }
                                if (isSelected) {
                                    Icon(
                                        imageVector = Icons.Default.CheckCircle,
                                        contentDescription = null,
                                        tint = AccentCyan,
                                        modifier = Modifier.size(18.dp)
                                    )
                                }
                            }
                        }
                    }
                }
            }
        },
        confirmButton = {
            TextButton(onClick = onDismiss) {
                Text("إغلاق", color = PrimaryRed, fontWeight = FontWeight.Bold)
            }
        }
    )
}

@Composable
fun BottomNavBar(
    selectedTab: AppTab,
    onTabSelected: (AppTab) -> Unit
) {
    NavigationBar(
        containerColor = DarkSurface,
        contentColor = Color.White,
        tonalElevation = 8.dp
    ) {
        NavigationBarItem(
            selected = selectedTab == AppTab.LIVE_NOW,
            onClick = { onTabSelected(AppTab.LIVE_NOW) },
            icon = { Icon(Icons.Default.PlayCircleFilled, contentDescription = "يعرض الآن") },
            label = { Text("يعرض الآن", fontSize = 11.sp, fontWeight = FontWeight.Bold) },
            colors = NavigationBarItemDefaults.colors(
                selectedIconColor = PrimaryRed,
                selectedTextColor = PrimaryRed,
                indicatorColor = DarkSurfaceVariant,
                unselectedIconColor = TextSecondary,
                unselectedTextColor = TextSecondary
            )
        )
        NavigationBarItem(
            selected = selectedTab == AppTab.UP_NEXT,
            onClick = { onTabSelected(AppTab.UP_NEXT) },
            icon = { Icon(Icons.Default.Schedule, contentDescription = "التالي") },
            label = { Text("التالي", fontSize = 11.sp, fontWeight = FontWeight.Bold) },
            colors = NavigationBarItemDefaults.colors(
                selectedIconColor = AccentCyan,
                selectedTextColor = AccentCyan,
                indicatorColor = DarkSurfaceVariant,
                unselectedIconColor = TextSecondary,
                unselectedTextColor = TextSecondary
            )
        )
        NavigationBarItem(
            selected = selectedTab == AppTab.ALL_SHOWS,
            onClick = { onTabSelected(AppTab.ALL_SHOWS) },
            icon = { Icon(Icons.Default.Movie, contentDescription = "العروض") },
            label = { Text("العروض والأفلام", fontSize = 11.sp, fontWeight = FontWeight.Bold) },
            colors = NavigationBarItemDefaults.colors(
                selectedIconColor = AccentGold,
                selectedTextColor = AccentGold,
                indicatorColor = DarkSurfaceVariant,
                unselectedIconColor = TextSecondary,
                unselectedTextColor = TextSecondary
            )
        )
        NavigationBarItem(
            selected = selectedTab == AppTab.CHANNELS,
            onClick = { onTabSelected(AppTab.CHANNELS) },
            icon = { Icon(Icons.Default.Tv, contentDescription = "القنوات") },
            label = { Text("القنوات", fontSize = 11.sp, fontWeight = FontWeight.Bold) },
            colors = NavigationBarItemDefaults.colors(
                selectedIconColor = Color(0xFF4CAF50),
                selectedTextColor = Color(0xFF4CAF50),
                indicatorColor = DarkSurfaceVariant,
                unselectedIconColor = TextSecondary,
                unselectedTextColor = TextSecondary
            )
        )
    }
}

// -------------------------------------------------------------------------------------------------
// TAB 1: LIVE NOW TAB VIEW (3 CARDS PER ROW GRID)
// -------------------------------------------------------------------------------------------------
@Composable
fun LiveNowTabView(
    items: List<NowAiringItem>,
    onItemClick: (Long) -> Unit,
    onChannelClick: (Long) -> Unit
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(3),
        contentPadding = PaddingValues(12.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        modifier = Modifier.fillMaxSize()
    ) {
        item(span = { GridItemSpan(3) }) {
            Column(modifier = Modifier.padding(bottom = 6.dp)) {
                Text(
                    text = "البث المباشر الآن 🔴",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Text(
                    text = "${items.size} قناة تبث برامج وأفلام مباشرة في هذا التوقيت",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary
                )
            }
        }

        items(items) { item ->
            LiveCardGrid3(item = item, onClick = { onItemClick(item.contentId) })
        }
    }
}

@Composable
fun LiveCardGrid3(item: NowAiringItem, onClick: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        Card(
            shape = RoundedCornerShape(10.dp),
            colors = CardDefaults.cardColors(containerColor = DarkSurface),
            modifier = Modifier
                .fillMaxWidth()
                .height(150.dp)
        ) {
            Box(modifier = Modifier.fillMaxSize()) {
                AsyncImage(
                    model = item.posterUrl ?: item.backdropUrl ?: item.channelLogo,
                    contentDescription = item.title,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )

                // Top-end Live Badge
                Surface(
                    color = PrimaryRed,
                    shape = RoundedCornerShape(bottomStart = 6.dp),
                    modifier = Modifier.align(Alignment.TopEnd)
                ) {
                    Text(
                        text = "مباشر",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White,
                        modifier = Modifier.padding(horizontal = 5.dp, vertical = 2.dp)
                    )
                }

                // Channel Logo Bottom-Start
                Surface(
                    color = Color.Black.copy(alpha = 0.75f),
                    shape = RoundedCornerShape(topEnd = 6.dp),
                    modifier = Modifier.align(Alignment.BottomStart)
                ) {
                    Row(
                        modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        AsyncImage(
                            model = item.channelLogo,
                            contentDescription = item.channelName,
                            modifier = Modifier.size(14.dp)
                        )
                        Spacer(modifier = Modifier.width(3.dp))
                        Text(
                            text = item.channelName,
                            fontSize = 9.sp,
                            fontWeight = FontWeight.Bold,
                            color = Color.White,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(4.dp))

        Text(
            text = item.title,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = Color.White,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "${item.startTime} - ${item.endTime ?: "..."}",
                style = MaterialTheme.typography.labelSmall,
                color = AccentGold,
                fontSize = 9.sp
            )
            if (item.remainingMinutes > 0) {
                Text(
                    text = "متبقي ${item.remainingMinutes}د",
                    style = MaterialTheme.typography.labelSmall,
                    color = AccentCyan,
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }

        Spacer(modifier = Modifier.height(3.dp))

        LinearProgressIndicator(
            progress = { item.progressPercent / 100f },
            modifier = Modifier
                .fillMaxWidth()
                .height(3.dp)
                .clip(RoundedCornerShape(2.dp)),
            color = PrimaryRed,
            trackColor = BorderColor
        )
    }
}

// -------------------------------------------------------------------------------------------------
// TAB 2: UP NEXT TAB VIEW (3 CARDS PER ROW GRID)
// -------------------------------------------------------------------------------------------------
@Composable
fun UpNextTabView(
    items: List<NextAiringItem>,
    onItemClick: (Long) -> Unit,
    onChannelClick: (Long) -> Unit
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(3),
        contentPadding = PaddingValues(12.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        modifier = Modifier.fillMaxSize()
    ) {
        item(span = { GridItemSpan(3) }) {
            Column(modifier = Modifier.padding(bottom = 6.dp)) {
                Text(
                    text = "العروض القادمة (التالي) ⏰",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
                Text(
                    text = "مواعيد البرامج والأفلام التي ستبدأ بعد قليل",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary
                )
            }
        }

        items(items) { item ->
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable { onItemClick(item.contentId) }
            ) {
                Card(
                    shape = RoundedCornerShape(10.dp),
                    colors = CardDefaults.cardColors(containerColor = DarkSurface),
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(150.dp)
                ) {
                    Box(modifier = Modifier.fillMaxSize()) {
                        AsyncImage(
                            model = item.posterUrl ?: item.backdropPath ?: item.channelLogo,
                            contentDescription = item.title,
                            modifier = Modifier.fillMaxSize(),
                            contentScale = ContentScale.Crop
                        )

                        // Start Time Badge Top-End
                        Surface(
                            color = AccentCyan,
                            shape = RoundedCornerShape(bottomStart = 6.dp),
                            modifier = Modifier.align(Alignment.TopEnd)
                        ) {
                            Text(
                                text = item.startTime,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.Black,
                                modifier = Modifier.padding(horizontal = 5.dp, vertical = 2.dp)
                            )
                        }

                        // Channel Logo Bottom-Start
                        Surface(
                            color = Color.Black.copy(alpha = 0.75f),
                            shape = RoundedCornerShape(topEnd = 6.dp),
                            modifier = Modifier.align(Alignment.BottomStart)
                        ) {
                            Row(
                                modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                AsyncImage(
                                    model = item.channelLogo,
                                    contentDescription = item.channelName,
                                    modifier = Modifier.size(14.dp)
                                )
                                Spacer(modifier = Modifier.width(3.dp))
                                Text(
                                    text = item.channelName,
                                    fontSize = 9.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis
                                )
                            }
                        }
                    }
                }

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = item.title,
                    style = MaterialTheme.typography.labelSmall,
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )

                Text(
                    text = "يبدأ ${item.startTime}",
                    style = MaterialTheme.typography.labelSmall,
                    color = AccentCyan,
                    fontSize = 10.sp
                )
            }
        }
    }
}

// -------------------------------------------------------------------------------------------------
// TAB 3: ALL SHOWS & MOVIES TAB VIEW (3 CARDS PER ROW GRID)
// -------------------------------------------------------------------------------------------------
@Composable
fun AllShowsTabView(
    movies: List<Content>,
    selectedCategory: String,
    onCategorySelected: (String) -> Unit,
    onMovieClick: (Long) -> Unit
) {
    val categories = listOf(
        "all" to "الكل (${movies.size})",
        "movie" to "🎬 أفلام",
        "series" to "📺 مسلسلات",
        "documentary" to "🌍 وثائقيات",
        "sports" to "⚽ رياضة",
        "news" to "📰 أخبار",
        "kids" to "🧸 أطفال",
        "religious" to "🕌 إسلامية",
        "theatre" to "🎭 مسرحيات",
        "program" to "🎙️ برامج ومنوعات"
    )

    Column(modifier = Modifier.fillMaxSize()) {
        // Category Chips
        LazyRow(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 8.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(categories) { (key, title) ->
                FilterChip(
                    selected = selectedCategory == key,
                    onClick = { onCategorySelected(key) },
                    label = { Text(title, fontSize = 12.sp, fontWeight = FontWeight.Bold) },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = PrimaryRed,
                        selectedLabelColor = Color.White,
                        containerColor = DarkSurface,
                        labelColor = TextSecondary
                    )
                )
            }
        }

        // 3 Cards Per Row Grid
        LazyVerticalGrid(
            columns = GridCells.Fixed(3),
            contentPadding = PaddingValues(12.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier.fillMaxSize()
        ) {
            items(movies) { movie ->
                MoviePosterCardGrid3(movie = movie, onClick = { onMovieClick(movie.id) })
            }
        }
    }
}

@Composable
fun MoviePosterCardGrid3(movie: Content, onClick: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
    ) {
        Card(
            shape = RoundedCornerShape(10.dp),
            colors = CardDefaults.cardColors(containerColor = DarkSurface),
            modifier = Modifier
                .fillMaxWidth()
                .height(150.dp)
        ) {
            Box(modifier = Modifier.fillMaxSize()) {
                AsyncImage(
                    model = movie.posterUrl,
                    contentDescription = movie.titleAr,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )

                if (!movie.rating.isNullOrBlank()) {
                    Surface(
                        color = Color.Black.copy(alpha = 0.75f),
                        shape = RoundedCornerShape(bottomStart = 6.dp),
                        modifier = Modifier.align(Alignment.TopEnd)
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 4.dp, vertical = 2.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = Icons.Default.Star,
                                contentDescription = null,
                                tint = AccentGold,
                                modifier = Modifier.size(10.dp)
                            )
                            Spacer(modifier = Modifier.width(2.dp))
                            Text(
                                text = movie.rating,
                                fontSize = 10.sp,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(4.dp))

        Text(
            text = movie.titleAr,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = Color.White,
            maxLines = 1,
            overflow = TextOverflow.Ellipsis
        )

        if (movie.airings.isNotEmpty()) {
            Text(
                text = movie.airings.first().channelName,
                style = MaterialTheme.typography.labelSmall,
                color = AccentGold,
                fontSize = 10.sp,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

// -------------------------------------------------------------------------------------------------
// TAB 4: CHANNELS & FREQUENCIES TAB VIEW (3 CARDS PER ROW GRID + PAID CHANNELS TOGGLE)
// -------------------------------------------------------------------------------------------------
@Composable
fun ChannelsTabView(
    channels: List<Channel>,
    selectedCategory: String,
    showPaidChannels: Boolean,
    onTogglePaidChannels: (Boolean) -> Unit,
    onCategorySelected: (String) -> Unit,
    onChannelClick: (Long) -> Unit
) {
    val categories = listOf(
        "all" to "الكل (${channels.size})",
        "movies" to "🎬 سينما وأفلام",
        "series" to "📺 دراما ومسلسلات",
        "sports" to "⚽ رياضة",
        "general" to "🌐 عامة ومنوعات",
        "news" to "📰 أخبار",
        "kids" to "🧸 أطفال",
        "religious" to "🕌 إسلامية",
        "documentary" to "🌍 وثائقيات"
    )

    Column(modifier = Modifier.fillMaxSize()) {
        // Paid Channels Filter Toggle Card
        Surface(
            color = if (showPaidChannels) PrimaryRed.copy(alpha = 0.12f) else DarkSurface,
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 6.dp)
                .border(
                    width = 1.dp,
                    color = if (showPaidChannels) PrimaryRed.copy(alpha = 0.5f) else BorderColor,
                    shape = RoundedCornerShape(12.dp)
                )
                .clickable { onTogglePaidChannels(!showPaidChannels) }
        ) {
            Row(
                modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    modifier = Modifier.weight(1f)
                ) {
                    Icon(
                        imageVector = if (showPaidChannels) Icons.Default.LockOpen else Icons.Default.Lock,
                        contentDescription = null,
                        tint = if (showPaidChannels) PrimaryRed else AccentGold,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Column {
                        Text(
                            text = "القنوات المشفرة والمدفوعة (OSN & beIN)",
                            style = MaterialTheme.typography.bodySmall,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Text(
                            text = if (showPaidChannels) "مفعلة (تظهر القنوات المشفرة وعروضها)" else "معطلة (يتم عرض القنوات المجانية المفتوحة فقط)",
                            style = MaterialTheme.typography.labelSmall,
                            color = if (showPaidChannels) PrimaryRed else TextSecondary,
                            fontSize = 10.sp
                        )
                    }
                }
                Switch(
                    checked = showPaidChannels,
                    onCheckedChange = onTogglePaidChannels,
                    colors = SwitchDefaults.colors(
                        checkedThumbColor = Color.White,
                        checkedTrackColor = PrimaryRed,
                        uncheckedThumbColor = TextSecondary,
                        uncheckedTrackColor = DarkSurfaceVariant
                    )
                )
            }
        }

        // Channel Category Chips
        LazyRow(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 6.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            items(categories) { (key, title) ->
                FilterChip(
                    selected = selectedCategory == key,
                    onClick = { onCategorySelected(key) },
                    label = { Text(title, fontSize = 12.sp, fontWeight = FontWeight.Bold) },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = AccentCyan,
                        selectedLabelColor = Color.Black,
                        containerColor = DarkSurface,
                        labelColor = TextSecondary
                    )
                )
            }
        }

        // 3 Channels Per Row Grid
        LazyVerticalGrid(
            columns = GridCells.Fixed(3),
            contentPadding = PaddingValues(12.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            modifier = Modifier.fillMaxSize()
        ) {
            items(channels) { channel ->
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onChannelClick(channel.id) },
                    shape = RoundedCornerShape(12.dp),
                    colors = CardDefaults.cardColors(containerColor = DarkSurface)
                ) {
                    Box(modifier = Modifier.fillMaxSize()) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(10.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(55.dp)
                                    .background(DarkSurfaceVariant, CircleShape)
                                    .padding(6.dp),
                                contentAlignment = Alignment.Center
                            ) {
                                AsyncImage(
                                    model = channel.logoUrl,
                                    contentDescription = channel.displayName,
                                    modifier = Modifier.fillMaxSize(),
                                    contentScale = ContentScale.Fit
                                )
                            }

                            Spacer(modifier = Modifier.height(6.dp))

                            Text(
                                text = channel.displayName,
                                style = MaterialTheme.typography.labelSmall,
                                fontWeight = FontWeight.Bold,
                                color = Color.White,
                                textAlign = TextAlign.Center,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )

                            Spacer(modifier = Modifier.height(2.dp))

                            Text(
                                text = channel.quality ?: "HD",
                                style = MaterialTheme.typography.labelSmall,
                                color = AccentGold,
                                fontSize = 10.sp
                            )
                        }

                        // Paid Channel Badge Top-End
                        if (channel.isPaidChannel) {
                            Surface(
                                color = PrimaryRed,
                                shape = RoundedCornerShape(bottomStart = 6.dp),
                                modifier = Modifier.align(Alignment.TopEnd)
                            ) {
                                Text(
                                    text = "مشفرة",
                                    fontSize = 8.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White,
                                    modifier = Modifier.padding(horizontal = 4.dp, vertical = 1.dp)
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

// -------------------------------------------------------------------------------------------------
// UNIVERSAL INSTANT SEARCH RESULTS VIEW (3 CARDS PER ROW GRID)
// -------------------------------------------------------------------------------------------------
@Composable
fun SearchResultsView(
    query: String,
    searchResults: SearchResults,
    onMovieClick: (Long) -> Unit,
    onChannelClick: (Long) -> Unit
) {
    LazyVerticalGrid(
        columns = GridCells.Fixed(3),
        contentPadding = PaddingValues(12.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp),
        modifier = Modifier.fillMaxSize()
    ) {
        item(span = { GridItemSpan(3) }) {
            Text(
                text = "نتائج البحث الفوري عن: \"$query\"",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = AccentGold
            )
        }

        // 1. Matched Channels Section
        if (searchResults.channels.isNotEmpty()) {
            item(span = { GridItemSpan(3) }) {
                Text(
                    text = "📡 القنوات المطابقة (${searchResults.channels.size}):",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    modifier = Modifier.padding(top = 8.dp)
                )
            }

            items(searchResults.channels) { channel ->
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { onChannelClick(channel.id) },
                    shape = RoundedCornerShape(10.dp),
                    colors = CardDefaults.cardColors(containerColor = DarkSurface)
                ) {
                    Column(
                        modifier = Modifier.padding(8.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        AsyncImage(
                            model = channel.logoUrl,
                            contentDescription = channel.displayName,
                            modifier = Modifier.size(45.dp),
                            contentScale = ContentScale.Fit
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = channel.displayName,
                            style = MaterialTheme.typography.labelSmall,
                            fontWeight = FontWeight.Bold,
                            color = Color.White,
                            textAlign = TextAlign.Center,
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
            }
        }

        // 2. Matched Shows / Movies / Actors Section (3 Cards Per Row)
        if (searchResults.shows.isNotEmpty()) {
            item(span = { GridItemSpan(3) }) {
                Text(
                    text = "🎬 العروض والمسلسلات والممثلين (${searchResults.shows.size}):",
                    style = MaterialTheme.typography.titleSmall,
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    modifier = Modifier.padding(top = 12.dp)
                )
            }

            items(searchResults.shows) { show ->
                MoviePosterCardGrid3(movie = show, onClick = { onMovieClick(show.id) })
            }
        }

        if (searchResults.channels.isEmpty() && searchResults.shows.isEmpty()) {
            item(span = { GridItemSpan(3) }) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 60.dp),
                    contentAlignment = Alignment.Center
                ) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Icon(
                            imageVector = Icons.Default.SearchOff,
                            contentDescription = null,
                            tint = TextSecondary,
                            modifier = Modifier.size(48.dp)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = "لا توجد نتائج مطابقة لـ \"$query\"",
                            color = TextSecondary,
                            fontSize = 14.sp
                        )
                    }
                }
            }
        }
    }
}
