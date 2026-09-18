package com.tvguide.app.ui.components

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.window.DialogProperties
import coil.compose.AsyncImage
import com.tvguide.app.data.models.Channel
import com.tvguide.app.ui.theme.*

private val CardSurface = Color(0xFF1E212B)

private enum class SettingsTab {
    CATEGORIES,
    FAVORITES,
    HIDDEN
}

@Composable
fun SettingsDialog(
    allChannels: List<Channel>,
    categoryOrder: List<String>,
    onCategoryOrderChange: (List<String>) -> Unit,
    favoriteChannelIds: List<Long>,
    onToggleFavorite: (Long) -> Unit,
    onMoveFavorite: (Int, Int) -> Unit,
    hiddenChannelIds: Set<Long>,
    onToggleHideChannel: (Long) -> Unit,
    onUnhideAllChannels: () -> Unit,
    onDismiss: () -> Unit
) {
    var activeTab by remember { mutableStateOf(SettingsTab.CATEGORIES) }
    var channelSearchQuery by remember { mutableStateOf("") }

    Dialog(
        onDismissRequest = onDismiss,
        properties = DialogProperties(usePlatformDefaultWidth = false)
    ) {
        Card(
            modifier = Modifier
                .fillMaxWidth(0.95f)
                .fillMaxHeight(0.88f)
                .padding(vertical = 16.dp),
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = DarkSurface)
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(16.dp)
            ) {
                // Header
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    IconButton(
                        onClick = onDismiss,
                        modifier = Modifier
                            .size(32.dp)
                            .background(DarkSurfaceVariant, CircleShape)
                    ) {
                        Icon(
                            imageVector = Icons.Default.Close,
                            contentDescription = "Close",
                            tint = Color.White,
                            modifier = Modifier.size(18.dp)
                        )
                    }

                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(horizontalAlignment = Alignment.End) {
                            Text(
                                text = "إعدادات وتخصيص الدليل",
                                color = Color.White,
                                fontSize = 17.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = "تحكم في أولوياتك وترتيب القنوات",
                                color = TextSecondary,
                                fontSize = 12.sp
                            )
                        }
                        Spacer(modifier = Modifier.width(10.dp))
                        Box(
                            modifier = Modifier
                                .size(38.dp)
                                .background(PrimaryRed.copy(alpha = 0.15f), RoundedCornerShape(10.dp)),
                            contentAlignment = Alignment.Center
                        ) {
                            Icon(
                                imageVector = Icons.Default.Tune,
                                contentDescription = null,
                                tint = PrimaryRed,
                                modifier = Modifier.size(22.dp)
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(14.dp))

                // Custom Tab Bar
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .background(DarkSurfaceVariant, RoundedCornerShape(12.dp))
                        .padding(4.dp),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    TabButton(
                        text = "أولويات المحتوى",
                        icon = Icons.Default.Sort,
                        isSelected = activeTab == SettingsTab.CATEGORIES,
                        onClick = { activeTab = SettingsTab.CATEGORIES },
                        modifier = Modifier.weight(1f)
                    )
                    TabButton(
                        text = "المفضلة (${favoriteChannelIds.size})",
                        icon = Icons.Default.Star,
                        isSelected = activeTab == SettingsTab.FAVORITES,
                        onClick = { activeTab = SettingsTab.FAVORITES },
                        modifier = Modifier.weight(1f)
                    )
                    TabButton(
                        text = "المحظورة (${hiddenChannelIds.size})",
                        icon = Icons.Default.VisibilityOff,
                        isSelected = activeTab == SettingsTab.HIDDEN,
                        onClick = { activeTab = SettingsTab.HIDDEN },
                        modifier = Modifier.weight(1f)
                    )
                }

                Spacer(modifier = Modifier.height(12.dp))

                // Content Area
                Box(modifier = Modifier.weight(1f)) {
                    when (activeTab) {
                        SettingsTab.CATEGORIES -> {
                            CategoriesReorderSection(
                                categoryOrder = categoryOrder,
                                onReorder = onCategoryOrderChange
                            )
                        }
                        SettingsTab.FAVORITES -> {
                            FavoritesSection(
                                allChannels = allChannels,
                                favoriteChannelIds = favoriteChannelIds,
                                searchQuery = channelSearchQuery,
                                onSearchChange = { channelSearchQuery = it },
                                onToggleFavorite = onToggleFavorite,
                                onMoveFavorite = onMoveFavorite
                            )
                        }
                        SettingsTab.HIDDEN -> {
                            HiddenChannelsSection(
                                allChannels = allChannels,
                                hiddenChannelIds = hiddenChannelIds,
                                searchQuery = channelSearchQuery,
                                onSearchChange = { channelSearchQuery = it },
                                onToggleHide = onToggleHideChannel,
                                onUnhideAll = onUnhideAllChannels
                            )
                        }
                    }
                }

                Spacer(modifier = Modifier.height(10.dp))

                // Bottom Done Button
                Button(
                    onClick = onDismiss,
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(44.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = PrimaryRed),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Text(
                        text = "حفظ وإغلاق",
                        color = Color.White,
                        fontSize = 15.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

@Composable
private fun TabButton(
    text: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    isSelected: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .height(36.dp)
            .clip(RoundedCornerShape(9.dp))
            .background(if (isSelected) PrimaryRed else Color.Transparent)
            .clickable(onClick = onClick),
        contentAlignment = Alignment.Center
    ) {
        Row(
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = if (isSelected) Color.White else TextSecondary,
                modifier = Modifier.size(14.dp)
            )
            Spacer(modifier = Modifier.width(4.dp))
            Text(
                text = text,
                color = if (isSelected) Color.White else TextSecondary,
                fontSize = 11.5.sp,
                fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )
        }
    }
}

// -------------------------------------------------------------------------------------------------
// 1. CATEGORIES REORDER SECTION
// -------------------------------------------------------------------------------------------------

@Composable
private fun CategoriesReorderSection(
    categoryOrder: List<String>,
    onReorder: (List<String>) -> Unit
) {
    val categoryMeta = mapOf(
        "movie" to Triple("أفلام سينمائية", "عروض الأفلام العربية والعالمية", Icons.Default.Movie),
        "series" to Triple("مسلسلات ودراما", "المسلسلات العربية والتركية والأجنبية", Icons.Default.Tv),
        "cartoon" to Triple("كارتون وأطفال", "رسوم متحركة وبرامج عائلية", Icons.Default.ChildCare),
        "other" to Triple("برامج ومنوعات", "برامج حوارية، وثائقية، وتوك شو", Icons.Default.Mic)
    )

    Column(modifier = Modifier.fillMaxSize()) {
        Surface(
            color = DarkSurfaceVariant.copy(alpha = 0.5f),
            shape = RoundedCornerShape(12.dp),
            modifier = Modifier.fillMaxWidth()
        ) {
            Row(
                modifier = Modifier.padding(10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Icon(
                    imageVector = Icons.Default.Info,
                    contentDescription = null,
                    tint = AccentCyan,
                    modifier = Modifier.size(16.dp)
                )
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "حدد أولوية ظهور العروض في الصفحة الرئيسية. التصنيف الأول سيظهر دائماً في صدارة شاشة (يعرض الآن) و(العروض).",
                    color = TextSecondary,
                    fontSize = 11.5.sp,
                    lineHeight = 16.sp
                )
            }
        }

        Spacer(modifier = Modifier.height(14.dp))

        LazyColumn(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            itemsIndexed(categoryOrder) { index, catKey ->
                val meta = categoryMeta[catKey] ?: Triple(catKey, "", Icons.Default.Category)
                val rank = index + 1

                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(14.dp),
                    colors = CardDefaults.cardColors(containerColor = CardSurface),
                    border = androidx.compose.foundation.BorderStroke(
                        1.dp,
                        if (rank == 1) PrimaryRed.copy(alpha = 0.5f) else Color.White.copy(alpha = 0.06f)
                    )
                ) {
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        // Reorder arrows
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            IconButton(
                                onClick = {
                                    if (index > 0) {
                                        val mutable = categoryOrder.toMutableList()
                                        val item = mutable.removeAt(index)
                                        mutable.add(index - 1, item)
                                        onReorder(mutable)
                                    }
                                },
                                enabled = index > 0,
                                modifier = Modifier.size(24.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.KeyboardArrowUp,
                                    contentDescription = "Move Up",
                                    tint = if (index > 0) AccentGold else Color.Gray.copy(alpha = 0.3f),
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                            IconButton(
                                onClick = {
                                    if (index < categoryOrder.size - 1) {
                                        val mutable = categoryOrder.toMutableList()
                                        val item = mutable.removeAt(index)
                                        mutable.add(index + 1, item)
                                        onReorder(mutable)
                                    }
                                },
                                enabled = index < categoryOrder.size - 1,
                                modifier = Modifier.size(24.dp)
                            ) {
                                Icon(
                                    imageVector = Icons.Default.KeyboardArrowDown,
                                    contentDescription = "Move Down",
                                    tint = if (index < categoryOrder.size - 1) AccentGold else Color.Gray.copy(alpha = 0.3f),
                                    modifier = Modifier.size(20.dp)
                                )
                            }
                        }

                        Spacer(modifier = Modifier.width(8.dp))

                        // Category info
                        Column(modifier = Modifier.weight(1f)) {
                            Text(
                                text = meta.first,
                                color = Color.White,
                                fontSize = 14.sp,
                                fontWeight = FontWeight.Bold
                            )
                            Text(
                                text = meta.second,
                                color = TextSecondary,
                                fontSize = 11.sp,
                                maxLines = 1,
                                overflow = TextOverflow.Ellipsis
                            )
                        }

                        Spacer(modifier = Modifier.width(8.dp))

                        // Rank Badge
                        Box(
                            modifier = Modifier
                                .size(28.dp)
                                .background(
                                    if (rank == 1) PrimaryRed else DarkSurfaceVariant,
                                    CircleShape
                                ),
                            contentAlignment = Alignment.Center
                        ) {
                            Text(
                                text = "#$rank",
                                color = Color.White,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                    }
                }
            }
        }
    }
}

// -------------------------------------------------------------------------------------------------
// 2. FAVORITES SECTION
// -------------------------------------------------------------------------------------------------

@Composable
private fun FavoritesSection(
    allChannels: List<Channel>,
    favoriteChannelIds: List<Long>,
    searchQuery: String,
    onSearchChange: (String) -> Unit,
    onToggleFavorite: (Long) -> Unit,
    onMoveFavorite: (Int, Int) -> Unit
) {
    val channelMap = remember(allChannels) { allChannels.associateBy { it.id } }
    val favChannels = remember(favoriteChannelIds, channelMap) {
        favoriteChannelIds.mapNotNull { channelMap[it] }
    }

    val filteredAll = remember(allChannels, searchQuery) {
        if (searchQuery.isBlank()) allChannels
        else allChannels.filter {
            it.displayName.contains(searchQuery, ignoreCase = true) ||
                    (it.nameEn ?: "").contains(searchQuery, ignoreCase = true)
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        // Search bar
        OutlinedTextField(
            value = searchQuery,
            onValueChange = onSearchChange,
            placeholder = { Text("ابحث عن قناة لإضافتها للمفضلة...", fontSize = 12.sp, color = TextSecondary) },
            singleLine = true,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = PrimaryRed,
                unfocusedBorderColor = Color.White.copy(alpha = 0.1f),
                focusedContainerColor = DarkSurfaceVariant,
                unfocusedContainerColor = DarkSurfaceVariant
            ),
            shape = RoundedCornerShape(12.dp),
            leadingIcon = {
                Icon(Icons.Default.Search, contentDescription = null, tint = TextSecondary, modifier = Modifier.size(18.dp))
            }
        )

        Spacer(modifier = Modifier.height(10.dp))

        if (favChannels.isNotEmpty() && searchQuery.isBlank()) {
            Text(
                text = "ترتيب قنواتك المفضلة (تظهر في صدارة الدليل):",
                color = AccentGold,
                fontSize = 12.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.padding(bottom = 6.dp)
            )
        }

        LazyColumn(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            if (searchQuery.isBlank() && favChannels.isNotEmpty()) {
                // Display ordered favorites with up/down controls
                itemsIndexed(favChannels) { index, ch ->
                    FavoriteChannelItem(
                        channel = ch,
                        isFavorite = true,
                        rank = index + 1,
                        canMoveUp = index > 0,
                        canMoveDown = index < favChannels.size - 1,
                        onMoveUp = { onMoveFavorite(index, index - 1) },
                        onMoveDown = { onMoveFavorite(index, index + 1) },
                        onToggle = { onToggleFavorite(ch.id) }
                    )
                }

                item {
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        text = "باقي القنوات (اضغط النجمة للإضافة):",
                        color = TextSecondary,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(bottom = 6.dp)
                    )
                }

                val nonFavs = allChannels.filter { !favoriteChannelIds.contains(it.id) }
                items(nonFavs) { ch ->
                    ChannelToggleItem(
                        channel = ch,
                        isActive = false,
                        activeColor = AccentGold,
                        activeIcon = Icons.Default.Star,
                        inactiveIcon = Icons.Default.StarBorder,
                        onToggle = { onToggleFavorite(ch.id) }
                    )
                }
            } else {
                items(filteredAll) { ch ->
                    val isFav = favoriteChannelIds.contains(ch.id)
                    ChannelToggleItem(
                        channel = ch,
                        isActive = isFav,
                        activeColor = AccentGold,
                        activeIcon = Icons.Default.Star,
                        inactiveIcon = Icons.Default.StarBorder,
                        onToggle = { onToggleFavorite(ch.id) }
                    )
                }
            }
        }
    }
}

// -------------------------------------------------------------------------------------------------
// 3. HIDDEN CHANNELS SECTION
// -------------------------------------------------------------------------------------------------

@Composable
private fun HiddenChannelsSection(
    allChannels: List<Channel>,
    hiddenChannelIds: Set<Long>,
    searchQuery: String,
    onSearchChange: (String) -> Unit,
    onToggleHide: (Long) -> Unit,
    onUnhideAll: () -> Unit
) {
    val filteredChannels = remember(allChannels, searchQuery) {
        if (searchQuery.isBlank()) allChannels
        else allChannels.filter {
            it.displayName.contains(searchQuery, ignoreCase = true) ||
                    (it.nameEn ?: "").contains(searchQuery, ignoreCase = true)
        }
    }

    Column(modifier = Modifier.fillMaxSize()) {
        // Warning Banner
        if (hiddenChannelIds.isNotEmpty()) {
            Surface(
                color = PrimaryRed.copy(alpha = 0.15f),
                shape = RoundedCornerShape(12.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Row(
                    modifier = Modifier.padding(10.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    TextButton(onClick = onUnhideAll) {
                        Text("إظهار الكل", color = AccentCyan, fontSize = 12.sp, fontWeight = FontWeight.Bold)
                    }
                    Text(
                        text = "تم حظر ${hiddenChannelIds.size} قناة من الظهور في التطبيق",
                        color = PrimaryRed,
                        fontSize = 12.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
            Spacer(modifier = Modifier.height(10.dp))
        }

        // Search bar
        OutlinedTextField(
            value = searchQuery,
            onValueChange = onSearchChange,
            placeholder = { Text("ابحث عن قناة لحظرها أو إظهارها...", fontSize = 12.sp, color = TextSecondary) },
            singleLine = true,
            modifier = Modifier
                .fillMaxWidth()
                .height(48.dp),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor = PrimaryRed,
                unfocusedBorderColor = Color.White.copy(alpha = 0.1f),
                focusedContainerColor = DarkSurfaceVariant,
                unfocusedContainerColor = DarkSurfaceVariant
            ),
            shape = RoundedCornerShape(12.dp),
            leadingIcon = {
                Icon(Icons.Default.Search, contentDescription = null, tint = TextSecondary, modifier = Modifier.size(18.dp))
            }
        )

        Spacer(modifier = Modifier.height(10.dp))

        LazyColumn(
            modifier = Modifier.weight(1f),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            items(filteredChannels) { ch ->
                val isHidden = hiddenChannelIds.contains(ch.id)
                ChannelToggleItem(
                    channel = ch,
                    isActive = isHidden,
                    activeColor = PrimaryRed,
                    activeIcon = Icons.Default.VisibilityOff,
                    inactiveIcon = Icons.Default.Visibility,
                    subtitle = if (isHidden) "محظورة من الظهور" else "ظاهرة في الدليل",
                    onToggle = { onToggleHide(ch.id) }
                )
            }
        }
    }
}

// -------------------------------------------------------------------------------------------------
// REUSABLE CHANNEL ITEMS
// -------------------------------------------------------------------------------------------------

@Composable
private fun FavoriteChannelItem(
    channel: Channel,
    isFavorite: Boolean,
    rank: Int,
    canMoveUp: Boolean,
    canMoveDown: Boolean,
    onMoveUp: () -> Unit,
    onMoveDown: () -> Unit,
    onToggle: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = CardSurface)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 10.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            // Reorder controls
            Row(verticalAlignment = Alignment.CenterVertically) {
                IconButton(
                    onClick = onMoveUp,
                    enabled = canMoveUp,
                    modifier = Modifier.size(24.dp)
                ) {
                    Icon(
                        Icons.Default.KeyboardArrowUp,
                        contentDescription = "Up",
                        tint = if (canMoveUp) AccentGold else Color.Gray.copy(alpha = 0.3f),
                        modifier = Modifier.size(18.dp)
                    )
                }
                IconButton(
                    onClick = onMoveDown,
                    enabled = canMoveDown,
                    modifier = Modifier.size(24.dp)
                ) {
                    Icon(
                        Icons.Default.KeyboardArrowDown,
                        contentDescription = "Down",
                        tint = if (canMoveDown) AccentGold else Color.Gray.copy(alpha = 0.3f),
                        modifier = Modifier.size(18.dp)
                    )
                }
            }

            Spacer(modifier = Modifier.width(6.dp))

            // Star toggle
            IconButton(onClick = onToggle, modifier = Modifier.size(28.dp)) {
                Icon(
                    imageVector = Icons.Default.Star,
                    contentDescription = "Remove Favorite",
                    tint = AccentGold,
                    modifier = Modifier.size(20.dp)
                )
            }

            Spacer(modifier = Modifier.width(8.dp))

            // Channel Name
            Text(
                text = channel.displayName,
                color = Color.White,
                fontSize = 13.5.sp,
                fontWeight = FontWeight.Bold,
                modifier = Modifier.weight(1f),
                maxLines = 1,
                overflow = TextOverflow.Ellipsis
            )

            // Logo
            AsyncImage(
                model = channel.logoUrl,
                contentDescription = null,
                contentScale = ContentScale.Fit,
                modifier = Modifier
                    .size(28.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(Color.White.copy(alpha = 0.05f))
            )

            Spacer(modifier = Modifier.width(8.dp))

            // Rank badge
            Box(
                modifier = Modifier
                    .size(22.dp)
                    .background(AccentGold.copy(alpha = 0.2f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    text = "$rank",
                    color = AccentGold,
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        }
    }
}

@Composable
private fun ChannelToggleItem(
    channel: Channel,
    isActive: Boolean,
    activeColor: Color,
    activeIcon: androidx.compose.ui.graphics.vector.ImageVector,
    inactiveIcon: androidx.compose.ui.graphics.vector.ImageVector,
    subtitle: String? = null,
    onToggle: () -> Unit
) {
    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onToggle),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(
            containerColor = if (isActive) activeColor.copy(alpha = 0.12f) else CardSurface
        ),
        border = if (isActive) androidx.compose.foundation.BorderStroke(1.dp, activeColor.copy(alpha = 0.3f)) else null
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 12.dp, vertical = 8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            IconButton(onClick = onToggle, modifier = Modifier.size(28.dp)) {
                Icon(
                    imageVector = if (isActive) activeIcon else inactiveIcon,
                    contentDescription = null,
                    tint = if (isActive) activeColor else TextSecondary,
                    modifier = Modifier.size(20.dp)
                )
            }

            Spacer(modifier = Modifier.width(8.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(
                    text = channel.displayName,
                    color = Color.White,
                    fontSize = 13.5.sp,
                    fontWeight = FontWeight.Medium,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis
                )
                if (subtitle != null) {
                    Text(
                        text = subtitle,
                        color = if (isActive) activeColor else TextSecondary,
                        fontSize = 10.5.sp
                    )
                }
            }

            Spacer(modifier = Modifier.width(8.dp))

            AsyncImage(
                model = channel.logoUrl,
                contentDescription = null,
                contentScale = ContentScale.Fit,
                modifier = Modifier
                    .size(28.dp)
                    .clip(RoundedCornerShape(6.dp))
                    .background(Color.White.copy(alpha = 0.05f))
            )
        }
    }
}

