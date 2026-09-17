package com.tvguide.app.ui.screens

import android.Manifest
import android.os.Build
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.tvguide.app.data.models.Airing
import com.tvguide.app.data.models.Channel
import com.tvguide.app.data.models.Frequency
import com.tvguide.app.ui.components.ReminderOptionsDialog
import com.tvguide.app.ui.theme.*
import com.tvguide.app.util.ReminderManager
import java.util.Calendar

enum class AiringStatus {
    LIVE,
    ENDED,
    UPCOMING
}

private fun parseDateAndTimeToMillis(dateStr: String?, timeStr: String?, allowNextDay: Boolean = false): Long {
    if (dateStr.isNullOrBlank() || timeStr.isNullOrBlank()) return 0L
    return try {
        val dParts = dateStr.split("-").mapNotNull { it.toIntOrNull() }
        val tParts = timeStr.split(":").mapNotNull { it.toIntOrNull() }
        if (dParts.size == 3 && tParts.size >= 2) {
            val cal = Calendar.getInstance()
            cal.set(dParts[0], dParts[1] - 1, dParts[2], tParts[0], tParts[1], 0)
            cal.set(Calendar.MILLISECOND, 0)
            if (allowNextDay) cal.add(Calendar.DAY_OF_MONTH, 1)
            cal.timeInMillis
        } else 0L
    } catch (e: Exception) {
        0L
    }
}

fun calculateAiringStatus(date: String?, startTime: String?, endTime: String?): AiringStatus {
    if (startTime.isNullOrBlank()) return AiringStatus.UPCOMING
    val now = Calendar.getInstance()
    val nowMillis = now.timeInMillis
    val todayStr = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.getDefault()).format(now.time)
    val d = if (!date.isNullOrBlank() && date.contains("-")) date else todayStr

    val et = endTime ?: startTime
    val sParts = startTime.split(":").mapNotNull { it.toIntOrNull() }
    val eParts = et.split(":").mapNotNull { it.toIntOrNull() }
    val isCrossingMidnight = if (sParts.size >= 2 && eParts.size >= 2) {
        (eParts[0] * 60 + eParts[1]) < (sParts[0] * 60 + sParts[1])
    } else false

    val sMillis = parseDateAndTimeToMillis(d, startTime)
    val eMillis = parseDateAndTimeToMillis(d, et, allowNextDay = isCrossingMidnight)

    if (sMillis == 0L || eMillis == 0L) return AiringStatus.UPCOMING

    return when {
        nowMillis in sMillis until eMillis -> AiringStatus.LIVE
        nowMillis >= eMillis -> AiringStatus.ENDED
        else -> AiringStatus.UPCOMING
    }
}

fun calculateLiveMetrics(date: String?, startTime: String?, endTime: String?): Pair<Int, Int> {
    if (startTime.isNullOrBlank()) return Pair(50, 15)
    return try {
        val now = Calendar.getInstance()
        val nowMillis = now.timeInMillis
        val todayStr = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.getDefault()).format(now.time)
        val d = if (!date.isNullOrBlank() && date.contains("-")) date else todayStr

        val nonNullEt = if (!endTime.isNullOrBlank()) endTime else startTime
        val sParts = startTime.split(":").mapNotNull { it.toIntOrNull() }
        val eParts = nonNullEt.split(":").mapNotNull { it.toIntOrNull() }
        val isCrossingMidnight = if (sParts.size >= 2 && eParts.size >= 2) {
            (eParts[0] * 60 + eParts[1]) < (sParts[0] * 60 + sParts[1])
        } else false

        val sMillis = parseDateAndTimeToMillis(d, startTime)
        val eMillis = parseDateAndTimeToMillis(d, nonNullEt, allowNextDay = isCrossingMidnight)

        val totalDurationMin = ((eMillis - sMillis) / (60 * 1000)).toInt().coerceAtLeast(1)
        val elapsedMin = ((nowMillis - sMillis) / (60 * 1000)).toInt().coerceIn(0, totalDurationMin)
        val progress = ((elapsedMin * 100) / totalDurationMin).coerceIn(5, 95)
        val remaining = ((eMillis - nowMillis) / (60 * 1000)).toInt().coerceIn(1, 180)
        Pair(progress, remaining)
    } catch (e: Exception) {
        Pair(50, 15)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChannelDetailScreen(
    channel: Channel,
    schedule: List<Airing>,
    onBackClick: () -> Unit,
    onMovieClick: (Long) -> Unit
) {
    val context = LocalContext.current
    var showFrequencyModal by remember { mutableStateOf(false) }
    var airingForOptionsDialog by remember { mutableStateOf<Airing?>(null) }
    var pendingAiringForPermission by remember { mutableStateOf<Airing?>(null) }
    var refreshTrigger by remember { mutableStateOf(0) }

    val notificationPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            pendingAiringForPermission?.let { airing ->
                airingForOptionsDialog = airing
                pendingAiringForPermission = null
            }
        } else {
            Toast.makeText(context, "يرجى تفعيل إذن الإشعارات لاستلام التنبيهات", Toast.LENGTH_LONG).show()
        }
    }

    val listState = androidx.compose.foundation.lazy.rememberLazyListState()
    val liveIndex = remember(schedule) {
        schedule.indexOfFirst { calculateAiringStatus(it.date, it.startTime, it.endTime) == AiringStatus.LIVE }
    }
    val groupedSchedule = remember(schedule) {
        schedule.groupBy { it.date ?: "اليوم" }
    }

    LaunchedEffect(schedule, liveIndex) {
        if (liveIndex != -1) {
            listState.scrollToItem(
                index = (2 + liveIndex).coerceAtLeast(0),
                scrollOffset = -220
            )
        }
    }

    Scaffold(
        containerColor = DarkBackground,
        topBar = {
            TopAppBar(
                title = { Text(channel.displayName) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = Color.White)
                    }
                },
                actions = {
                    IconButton(onClick = { showFrequencyModal = true }) {
                        Icon(
                            Icons.Default.SatelliteAlt,
                            contentDescription = "Frequencies",
                            tint = AccentGold
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = DarkSurface,
                    titleContentColor = Color.White
                )
            )
        }
    ) { padding ->
        LazyColumn(
            state = listState,
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Channel Info Card
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = DarkSurface)
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Box(
                            modifier = Modifier
                                .size(64.dp)
                                .background(DarkSurfaceVariant, CircleShape)
                                .padding(8.dp),
                            contentAlignment = Alignment.Center
                        ) {
                            AsyncImage(
                                model = channel.logoUrl,
                                contentDescription = channel.displayName,
                                modifier = Modifier.fillMaxSize(),
                                contentScale = ContentScale.Fit
                            )
                        }
                        Spacer(modifier = Modifier.width(16.dp))
                        Column {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = channel.displayName,
                                    style = MaterialTheme.typography.titleLarge,
                                    fontWeight = FontWeight.Bold,
                                    color = Color.White
                                )
                                if (channel.isPaidChannel) {
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Surface(
                                        color = PrimaryRed,
                                        shape = RoundedCornerShape(6.dp)
                                    ) {
                                        Text(
                                            text = "مشفرة",
                                            color = Color.White,
                                            fontSize = 10.sp,
                                            fontWeight = FontWeight.Bold,
                                            modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                        )
                                    }
                                }
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Button(
                                onClick = { showFrequencyModal = true },
                                colors = ButtonDefaults.buttonColors(containerColor = DarkSurfaceVariant),
                                shape = RoundedCornerShape(8.dp),
                                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 6.dp)
                            ) {
                                Icon(
                                    Icons.Default.SatelliteAlt,
                                    contentDescription = null,
                                    tint = AccentGold,
                                    modifier = Modifier.size(16.dp)
                                )
                                Spacer(modifier = Modifier.width(6.dp))
                                Text("بيانات التردد والاستقبال", color = Color.White, fontSize = 12.sp)
                            }
                        }
                    }
                }
            }

            // Schedule Header
            item {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 8.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "جدول البث اليومي 📅",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Text(
                        text = if (schedule.isNotEmpty()) "${schedule.size} عروض مجدولة" else "غير متوفر حالياً",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary
                    )
                }
            }

            // Empty State Card when schedule has 0 airings
            if (schedule.isEmpty()) {
                item {
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(vertical = 16.dp),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(containerColor = DarkSurface)
                    ) {
                        Column(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(24.dp),
                            horizontalAlignment = Alignment.CenterHorizontally,
                            verticalArrangement = Arrangement.Center
                        ) {
                            Box(
                                modifier = Modifier
                                    .size(64.dp)
                                    .background(DarkSurfaceVariant, CircleShape),
                                contentAlignment = Alignment.Center
                            ) {
                                Icon(
                                    imageVector = Icons.Default.EventBusy,
                                    contentDescription = null,
                                    tint = AccentGold,
                                    modifier = Modifier.size(32.dp)
                                )
                            }
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                text = "لا يتوفر جدول بث لهذه القناة حالياً",
                                style = MaterialTheme.typography.titleMedium,
                                fontWeight = FontWeight.Bold,
                                color = Color.White
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "يمكنك متابعة البث التلفزيوني عبر تردد القناة وبيانات الاستقبال المتاحة أدناه، وسيتم تحديث جدول العروض فور توفره.",
                                style = MaterialTheme.typography.bodySmall,
                                color = TextSecondary,
                                textAlign = TextAlign.Center
                            )
                            Spacer(modifier = Modifier.height(18.dp))
                            Button(
                                onClick = { showFrequencyModal = true },
                                colors = ButtonDefaults.buttonColors(containerColor = DarkSurfaceVariant),
                                shape = RoundedCornerShape(8.dp),
                                contentPadding = PaddingValues(horizontal = 16.dp, vertical = 8.dp)
                            ) {
                                Icon(
                                    Icons.Default.SatelliteAlt,
                                    contentDescription = null,
                                    tint = AccentGold,
                                    modifier = Modifier.size(18.dp)
                                )
                                Spacer(modifier = Modifier.width(8.dp))
                                Text("عرض بيانات التردد والاستقبال", color = Color.White, fontSize = 13.sp)
                            }
                        }
                    }
                }
            }

            // Broadcast Items Grouped by Date (Multi-Day Chronological EPG)
            groupedSchedule.forEach { (dateStr, dateItems) ->
                item(key = "header_$dateStr") {
                    val cal = Calendar.getInstance()
                    val sdf = java.text.SimpleDateFormat("yyyy-MM-dd", java.util.Locale.getDefault())
                    val todayStr = sdf.format(cal.time)
                    cal.add(Calendar.DAY_OF_MONTH, 1)
                    val tomorrowStr = sdf.format(cal.time)

                    val headerTitle = when (dateStr) {
                        todayStr -> "اليوم 📅 ($dateStr)"
                        tomorrowStr -> "غداً 📅 ($dateStr)"
                        else -> "📅 $dateStr"
                    }

                    Surface(
                        color = DarkSurfaceVariant,
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(top = 10.dp, bottom = 4.dp)
                    ) {
                        Row(
                            modifier = Modifier.padding(horizontal = 12.dp, vertical = 8.dp),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Text(
                                text = headerTitle,
                                color = AccentGold,
                                fontWeight = FontWeight.Bold,
                                fontSize = 13.sp
                            )
                            Text(
                                text = "${dateItems.size} عروض",
                                color = TextSecondary,
                                fontSize = 11.sp
                            )
                        }
                    }
                }

                items(dateItems, key = { it.broadcastId }) { item ->
                    val status = calculateAiringStatus(item.date, item.startTime, item.endTime)
                    val isReminderSet = ReminderManager.isReminderSet(context, item.broadcastId)

                    when (status) {
                        AiringStatus.LIVE -> {
                            // 🔴 LIVE AIRING CARD (Distinct Vibrant Red Highlight & Progress Bar)
                            val (progress, remaining) = calculateLiveMetrics(item.date, item.startTime, item.endTime)
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .border(1.5.dp, PrimaryRed, RoundedCornerShape(12.dp))
                                .clickable { onMovieClick(item.contentId) },
                            shape = RoundedCornerShape(12.dp),
                            colors = CardDefaults.cardColors(containerColor = PrimaryRed.copy(alpha = 0.08f))
                        ) {
                            Column(modifier = Modifier.padding(12.dp)) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    val posterModel = if (!item.poster.isNullOrBlank()) item.poster else item.channelLogo
                                    if (!posterModel.isNullOrBlank()) {
                                        Box(
                                            modifier = Modifier
                                                .size(54.dp, 70.dp)
                                                .clip(RoundedCornerShape(8.dp))
                                                .background(DarkSurfaceVariant),
                                            contentAlignment = Alignment.Center
                                        ) {
                                            AsyncImage(
                                                model = posterModel,
                                                contentDescription = item.title,
                                                modifier = if (!item.poster.isNullOrBlank()) Modifier.fillMaxSize() else Modifier.fillMaxSize().padding(6.dp),
                                                contentScale = if (!item.poster.isNullOrBlank()) ContentScale.Crop else ContentScale.Fit
                                            )
                                        }
                                        Spacer(modifier = Modifier.width(12.dp))
                                    }
                                    Column(modifier = Modifier.weight(1f)) {
                                        Row(verticalAlignment = Alignment.CenterVertically) {
                                            Surface(
                                                color = PrimaryRed,
                                                shape = RoundedCornerShape(4.dp)
                                            ) {
                                                Text(
                                                    text = "🔴 مباشر الآن",
                                                    color = Color.White,
                                                    fontSize = 10.sp,
                                                    fontWeight = FontWeight.Bold,
                                                    modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                                )
                                            }
                                            if (remaining > 0) {
                                                Spacer(modifier = Modifier.width(8.dp))
                                                Text(
                                                    text = "متبقي $remaining دقيقة",
                                                    color = AccentCyan,
                                                    fontSize = 11.sp,
                                                    fontWeight = FontWeight.Bold
                                                )
                                            }
                                        }
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(
                                            text = item.title,
                                            style = MaterialTheme.typography.bodyLarge,
                                            fontWeight = FontWeight.Bold,
                                            color = Color.White,
                                            maxLines = 1,
                                            overflow = TextOverflow.Ellipsis
                                        )
                                        Spacer(modifier = Modifier.height(2.dp))
                                        Text(
                                            text = "${item.date} • من ${item.startTime} إلى ${item.endTime ?: "..."}",
                                            style = MaterialTheme.typography.bodySmall,
                                            color = AccentGold,
                                            fontSize = 11.sp
                                        )
                                    }
                                }

                                Spacer(modifier = Modifier.height(8.dp))

                                LinearProgressIndicator(
                                    progress = { progress / 100f },
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .height(4.dp)
                                        .clip(RoundedCornerShape(2.dp)),
                                    color = PrimaryRed,
                                    trackColor = DarkSurfaceVariant
                                )
                            }
                        }
                    }

                    AiringStatus.ENDED -> {
                        // ⚪ ENDED AIRING CARD (Faded / Dimmed / Grayed Out)
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .alpha(0.40f)
                                .clickable { onMovieClick(item.contentId) },
                            shape = RoundedCornerShape(12.dp),
                            colors = CardDefaults.cardColors(containerColor = DarkSurface.copy(alpha = 0.5f))
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                val posterModel = if (!item.poster.isNullOrBlank()) item.poster else item.channelLogo
                                if (!posterModel.isNullOrBlank()) {
                                    Box(
                                        modifier = Modifier
                                            .size(46.dp, 60.dp)
                                            .clip(RoundedCornerShape(8.dp))
                                            .background(DarkSurfaceVariant),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        AsyncImage(
                                            model = posterModel,
                                            contentDescription = item.title,
                                            modifier = if (!item.poster.isNullOrBlank()) Modifier.fillMaxSize() else Modifier.fillMaxSize().padding(5.dp),
                                            contentScale = if (!item.poster.isNullOrBlank()) ContentScale.Crop else ContentScale.Fit
                                        )
                                    }
                                    Spacer(modifier = Modifier.width(12.dp))
                                }
                                Column(modifier = Modifier.weight(1f)) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text(
                                            text = "انتهى",
                                            color = TextSecondary,
                                            fontSize = 10.sp
                                        )
                                    }
                                    Text(
                                        text = item.title,
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = TextSecondary,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                    Spacer(modifier = Modifier.height(2.dp))
                                    Text(
                                        text = "من ${item.startTime} إلى ${item.endTime ?: "..."}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = TextMuted,
                                        fontSize = 10.sp
                                    )
                                }
                                Surface(
                                    color = DarkSurfaceVariant.copy(alpha = 0.5f),
                                    shape = RoundedCornerShape(6.dp)
                                ) {
                                    Text(
                                        text = item.startTime,
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                        color = TextMuted,
                                        fontSize = 11.sp
                                    )
                                }
                            }
                        }
                    }

                    AiringStatus.UPCOMING -> {
                        // 🔵 UPCOMING AIRING CARD (Crisp + Reminder Button)
                        Card(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clickable { onMovieClick(item.contentId) },
                            shape = RoundedCornerShape(12.dp),
                            colors = CardDefaults.cardColors(containerColor = DarkSurface)
                        ) {
                            Row(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(12.dp),
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                val posterModel = if (!item.poster.isNullOrBlank()) item.poster else item.channelLogo
                                if (!posterModel.isNullOrBlank()) {
                                    Box(
                                        modifier = Modifier
                                            .size(50.dp, 65.dp)
                                            .clip(RoundedCornerShape(8.dp))
                                            .background(DarkSurfaceVariant),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        AsyncImage(
                                            model = posterModel,
                                            contentDescription = item.title,
                                            modifier = if (!item.poster.isNullOrBlank()) Modifier.fillMaxSize() else Modifier.fillMaxSize().padding(6.dp),
                                            contentScale = if (!item.poster.isNullOrBlank()) ContentScale.Crop else ContentScale.Fit
                                        )
                                    }
                                    Spacer(modifier = Modifier.width(12.dp))
                                }
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(
                                        text = item.title,
                                        style = MaterialTheme.typography.bodyLarge,
                                        fontWeight = FontWeight.Bold,
                                        color = Color.White,
                                        maxLines = 1,
                                        overflow = TextOverflow.Ellipsis
                                    )
                                    Spacer(modifier = Modifier.height(3.dp))
                                    Text(
                                        text = "${item.date} • من ${item.startTime}${if (!item.endTime.isNullOrBlank()) " إلى ${item.endTime}" else ""}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = TextSecondary,
                                        fontSize = 11.sp
                                    )
                                }

                                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                    // Reminder Button
                                    IconButton(
                                        onClick = {
                                            if (ReminderManager.isReminderSet(context, item.broadcastId)) {
                                                ReminderManager.cancelReminder(context, item.broadcastId, item.title)
                                                refreshTrigger++
                                            } else {
                                                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                                                    !ReminderManager.hasNotificationPermission(context)
                                                ) {
                                                    pendingAiringForPermission = item
                                                    notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                                                } else {
                                                    airingForOptionsDialog = item
                                                }
                                            }
                                        },
                                        modifier = Modifier.size(32.dp)
                                    ) {
                                        Icon(
                                            imageVector = if (isReminderSet) Icons.Default.NotificationsActive else Icons.Default.NotificationsNone,
                                            contentDescription = "Remind",
                                            tint = if (isReminderSet) AccentCyan else TextSecondary,
                                            modifier = Modifier.size(20.dp)
                                        )
                                    }

                                    Surface(
                                        color = DarkSurfaceVariant,
                                        shape = RoundedCornerShape(8.dp)
                                    ) {
                                        Text(
                                            text = item.startTime,
                                            modifier = Modifier.padding(horizontal = 8.dp, vertical = 5.dp),
                                            color = AccentCyan,
                                            fontWeight = FontWeight.Bold,
                                            fontSize = 12.sp
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

        // Reminder Timing Options Dialog
        airingForOptionsDialog?.let { airing ->
            ReminderOptionsDialog(
                showTitle = airing.title,
                channelName = channel.displayName,
                startTime = airing.startTime,
                onConfirm = { options ->
                    ReminderManager.setReminder(
                        context = context,
                        broadcastId = airing.broadcastId,
                        title = airing.title,
                        channelName = channel.displayName,
                        startTime = airing.startTime,
                        options = options
                    )
                    refreshTrigger++
                    airingForOptionsDialog = null
                },
                onDismiss = { airingForOptionsDialog = null }
            )
        }

        if (showFrequencyModal) {
            FrequencyDialog(
                channel = channel,
                onDismiss = { showFrequencyModal = false }
            )
        }
    }
}

@Composable
fun FrequencyDialog(
    channel: Channel,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = DarkSurface,
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(Icons.Default.SatelliteAlt, contentDescription = null, tint = AccentGold)
                Spacer(modifier = Modifier.width(8.dp))
                Text(
                    text = "تردد ${channel.displayName}",
                    color = Color.White,
                    fontSize = 18.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                if (channel.frequencies.isNotEmpty()) {
                    channel.frequencies.forEach { freq ->
                        FrequencyCard(freq = freq)
                    }
                } else if (!channel.frequency.isNullOrBlank()) {
                    Surface(
                        color = DarkSurfaceVariant,
                        shape = RoundedCornerShape(8.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(modifier = Modifier.padding(12.dp)) {
                            Text(text = "القمر: نايل سات (Nilesat 7.0°W)", color = Color.White, fontWeight = FontWeight.Bold)
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(text = "التردد: ${channel.frequency}", color = AccentCyan)
                            Text(text = "معدل الترميز: 27500", color = TextSecondary)
                            Text(text = "معامل التصحيح: 5/6", color = TextSecondary)
                        }
                    }
                } else {
                    Text("لا توجد بيانات تردد مسجلة لهذه القناة حالياً", color = TextSecondary)
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
fun FrequencyCard(freq: Frequency) {
    Surface(
        color = DarkSurfaceVariant,
        shape = RoundedCornerShape(10.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = freq.satellite ?: "Nilesat 7.0°W",
                    fontWeight = FontWeight.Bold,
                    color = Color.White,
                    fontSize = 14.sp
                )
                Surface(
                    color = PrimaryRed.copy(alpha = 0.2f),
                    shape = RoundedCornerShape(4.dp)
                ) {
                    Text(
                        text = freq.quality ?: "HD",
                        color = PrimaryRed,
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                    )
                }
            }
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Column {
                    Text("التردد", color = TextSecondary, fontSize = 11.sp)
                    Text("${freq.frequency ?: "11555"} ${freq.polarization ?: "V"}", color = AccentCyan, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                }
                Column {
                    Text("الترميز", color = TextSecondary, fontSize = 11.sp)
                    Text(freq.symbolRate ?: "27500", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                }
                Column {
                    Text("التصحيح", color = TextSecondary, fontSize = 11.sp)
                    Text(freq.fec ?: "5/6", color = Color.White, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                }
            }
        }
    }
}
