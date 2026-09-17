package com.tvguide.app.ui.screens

import android.Manifest
import android.os.Build
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
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
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.tvguide.app.data.models.Airing
import com.tvguide.app.data.models.CastMember
import com.tvguide.app.data.models.Content
import com.tvguide.app.ui.components.ReminderOptionsDialog
import com.tvguide.app.ui.theme.*
import com.tvguide.app.util.ReminderManager

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MovieDetailScreen(
    content: Content,
    isFavorite: Boolean,
    onToggleFavorite: () -> Unit,
    onBackClick: () -> Unit,
    onChannelClick: (Long) -> Unit,
    onUpdateCategory: (String) -> Unit = {},
    onHideShow: (String) -> Unit = {}
) {
    val context = LocalContext.current
    var airingForOptionsDialog by remember { mutableStateOf<Airing?>(null) }
    var pendingAiringForPermission by remember { mutableStateOf<Airing?>(null) }
    var refreshTrigger by remember { mutableStateOf(0) }
    var currentCategory by remember(content.contentType) { mutableStateOf(content.contentType) }
    var showCategoryDialog by remember { mutableStateOf(false) }
    var showHideConfirmation by remember { mutableStateOf(false) }

    val notificationPermissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            pendingAiringForPermission?.let { airing ->
                airingForOptionsDialog = airing
                pendingAiringForPermission = null
            }
        } else {
            Toast.makeText(
                context,
                "يرجى تفعيل إذن الإشعارات من إعدادات الهاتف لتصلك تنبيهات العروض",
                Toast.LENGTH_LONG
            ).show()
        }
    }

    Scaffold(
        containerColor = DarkBackground,
        topBar = {
            TopAppBar(
                title = { Text(content.titleAr, maxLines = 1) },
                navigationIcon = {
                    IconButton(onClick = onBackClick) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = Color.White)
                    }
                },
                actions = {
                    IconButton(onClick = { showHideConfirmation = true }) {
                        Icon(
                            imageVector = Icons.Default.VisibilityOff,
                            contentDescription = "لا أهتم بهذا العرض",
                            tint = TextSecondary
                        )
                    }
                    IconButton(onClick = onToggleFavorite) {
                        Icon(
                            imageVector = if (isFavorite) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                            contentDescription = "Favorite",
                            tint = if (isFavorite) PrimaryRed else Color.White
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = Color.Transparent,
                    titleContentColor = Color.White
                )
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding),
            contentPadding = PaddingValues(bottom = 60.dp)
        ) {
            // Hero Backdrop + Poster Header
            item {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(280.dp)
                ) {
                    AsyncImage(
                        model = content.backdropUrl ?: content.posterUrl,
                        contentDescription = content.titleAr,
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Crop
                    )
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .background(
                                Brush.verticalGradient(
                                    colors = listOf(Color.Transparent, DarkBackground),
                                    startY = 50f
                                )
                            )
                    )
                }

                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 16.dp)
                        .offset(y = (-60).dp),
                    horizontalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    // Poster Card
                    Card(
                        modifier = Modifier
                            .width(110.dp)
                            .height(160.dp),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        AsyncImage(
                            model = content.posterUrl,
                            contentDescription = content.titleAr,
                            modifier = Modifier.fillMaxSize(),
                            contentScale = ContentScale.Crop
                        )
                    }

                    // Metadata
                    Column(
                        modifier = Modifier
                            .weight(1f)
                            .padding(top = 60.dp)
                    ) {
                        Text(
                            text = content.titleAr,
                            style = MaterialTheme.typography.titleLarge,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        if (!content.titleEn.isNullOrEmpty()) {
                            Text(
                                text = content.titleEn,
                                style = MaterialTheme.typography.bodyMedium,
                                color = TextSecondary
                            )
                        }
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            // Category Tag (Clickable to Edit)
                            Surface(
                                color = when (currentCategory) {
                                    "movie" -> PrimaryRed.copy(alpha = 0.2f)
                                    "series" -> AccentCyan.copy(alpha = 0.2f)
                                    "cartoon", "kids" -> AccentGold.copy(alpha = 0.2f)
                                    else -> DarkSurfaceVariant
                                },
                                shape = RoundedCornerShape(8.dp),
                                border = BorderStroke(
                                    1.dp,
                                    when (currentCategory) {
                                        "movie" -> PrimaryRed
                                        "series" -> AccentCyan
                                        "cartoon", "kids" -> AccentGold
                                        else -> TextSecondary
                                    }
                                ),
                                modifier = Modifier.clickable { showCategoryDialog = true }
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Text(
                                        text = when (currentCategory) {
                                            "movie" -> "🎬 فيلم"
                                            "series" -> "📺 مسلسل"
                                            "cartoon", "kids" -> "🧸 كارتون"
                                            else -> "🎙️ منوعات"
                                        },
                                        fontSize = 11.sp,
                                        fontWeight = FontWeight.Bold,
                                        color = Color.White
                                    )
                                    Spacer(modifier = Modifier.width(4.dp))
                                    Icon(
                                        Icons.Default.Edit,
                                        contentDescription = "تعديل التصنيف",
                                        tint = TextSecondary,
                                        modifier = Modifier.size(11.dp)
                                    )
                                }
                            }

                            if (content.releaseYear != null) {
                                Surface(
                                    color = DarkSurfaceVariant,
                                    shape = RoundedCornerShape(6.dp)
                                ) {
                                    Text(
                                        text = content.releaseYear.toString(),
                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                                        fontSize = 11.sp,
                                        color = TextSecondary
                                    )
                                }
                            }

                            if (!content.rating.isNullOrBlank()) {
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(
                                        Icons.Default.Star,
                                        contentDescription = null,
                                        tint = AccentGold,
                                        modifier = Modifier.size(14.dp)
                                    )
                                    Spacer(modifier = Modifier.width(3.dp))
                                    Text(
                                        text = content.rating,
                                        fontWeight = FontWeight.Bold,
                                        fontSize = 12.sp,
                                        color = Color.White
                                    )
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(8.dp))
                        OutlinedButton(
                            onClick = { showHideConfirmation = true },
                            colors = ButtonDefaults.outlinedButtonColors(contentColor = TextSecondary),
                            border = BorderStroke(1.dp, BorderColor),
                            shape = RoundedCornerShape(8.dp),
                            contentPadding = PaddingValues(horizontal = 10.dp, vertical = 2.dp)
                        ) {
                            Icon(
                                Icons.Default.VisibilityOff,
                                contentDescription = null,
                                tint = TextSecondary,
                                modifier = Modifier.size(13.dp)
                            )
                            Spacer(modifier = Modifier.width(5.dp))
                            Text("لا أهتم بهذا العرض", fontSize = 11.sp, color = TextSecondary)
                        }
                    }
                }
            }

            // Overview
            if (!content.displayOverview.isNullOrEmpty()) {
                item {
                    Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)) {
                        Text(
                            text = "قصة العمل",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            text = content.displayOverview ?: "",
                            style = MaterialTheme.typography.bodyMedium,
                            color = TextSecondary,
                            lineHeight = 22.sp
                        )
                    }
                    Spacer(modifier = Modifier.height(16.dp))
                }
            }

            // TV Airings Section with Notification Permission Handler
            item {
                Column(modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(
                            text = "مواعيد العرض على التلفزيون 📺",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color.White
                        )
                        Surface(
                            color = PrimaryRed.copy(alpha = 0.2f),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Text(
                                text = "${content.airings.size} مواعيد بث",
                                color = PrimaryRed,
                                fontSize = 12.sp,
                                fontWeight = FontWeight.Bold,
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                            )
                        }
                    }
                    Spacer(modifier = Modifier.height(10.dp))

                    if (content.airings.isEmpty()) {
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(containerColor = DarkSurface)
                        ) {
                            Text(
                                text = "لا توجد مواعيد بث مجدولة حالياً لهذا المحتوى",
                                modifier = Modifier.padding(16.dp),
                                color = TextSecondary,
                                style = MaterialTheme.typography.bodyMedium
                            )
                        }
                    } else {
                        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                            content.airings.forEach { airing ->
                                AiringCardItemWithPermission(
                                    airing = airing,
                                    movieTitle = content.titleAr,
                                    refreshKey = refreshTrigger,
                                    onRemindClick = {
                                        if (ReminderManager.isReminderSet(context, airing.broadcastId)) {
                                            ReminderManager.cancelReminder(context, airing.broadcastId, content.titleAr)
                                            refreshTrigger++
                                        } else {
                                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
                                                !ReminderManager.hasNotificationPermission(context)
                                            ) {
                                                pendingAiringForPermission = airing
                                                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
                                            } else {
                                                airingForOptionsDialog = airing
                                            }
                                        }
                                    },
                                    onClick = { onChannelClick(airing.channelId) }
                                )
                            }
                        }
                    }
                }
                Spacer(modifier = Modifier.height(20.dp))
            }

            // Cast Section with Photos
            if (content.cast.isNotEmpty()) {
                item {
                    Column(modifier = Modifier.padding(vertical = 8.dp)) {
                        Text(
                            text = "طاقم العمل والتمثيل 🎭",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = Color.White,
                            modifier = Modifier.padding(horizontal = 16.dp)
                        )
                        Spacer(modifier = Modifier.height(10.dp))
                        LazyRow(
                            contentPadding = PaddingValues(horizontal = 16.dp),
                            horizontalArrangement = Arrangement.spacedBy(14.dp)
                        ) {
                            items(content.cast) { actor ->
                                CastMemberItem(actor = actor)
                            }
                        }
                    }
                }
            }
        }

        // Reminder Timing Options Dialog
        airingForOptionsDialog?.let { airing ->
            ReminderOptionsDialog(
                showTitle = content.titleAr,
                channelName = airing.channelName,
                startTime = airing.startTime,
                onConfirm = { options ->
                    ReminderManager.setReminder(
                        context = context,
                        broadcastId = airing.broadcastId,
                        title = content.titleAr,
                        channelName = airing.channelName,
                        startTime = airing.startTime,
                        options = options
                    )
                    refreshTrigger++
                    airingForOptionsDialog = null
                },
                onDismiss = { airingForOptionsDialog = null }
            )
        }

        // Category Selection Dialog
        if (showCategoryDialog) {
            AlertDialog(
                onDismissRequest = { showCategoryDialog = false },
                title = {
                    Text(
                        text = "تعديل تصنيف العرض 🏷️",
                        fontWeight = FontWeight.Bold,
                        style = MaterialTheme.typography.titleMedium
                    )
                },
                text = {
                    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(
                            text = "حدد التصنيف الصحيح لـ \"${content.titleAr}\" لتحديث ظهوره وأولويته في التطبيق:",
                            fontSize = 13.sp,
                            color = TextSecondary
                        )
                        Spacer(modifier = Modifier.height(6.dp))
                        val categories = listOf(
                            Triple("movie", "🎬 فيلم (عربي أو أجنبي)", PrimaryRed),
                            Triple("series", "📺 مسلسل (عربي أو أجنبي)", AccentCyan),
                            Triple("cartoon", "🧸 كارتون وأطفال", AccentGold),
                            Triple("other", "🎙️ منوعات وبرامج وتوك شو", Color.LightGray)
                        )
                        categories.forEach { (catKey, catLabel, catColor) ->
                            val isSelected = currentCategory == catKey
                            Surface(
                                color = if (isSelected) catColor.copy(alpha = 0.2f) else DarkSurfaceVariant,
                                shape = RoundedCornerShape(10.dp),
                                border = BorderStroke(
                                    1.dp,
                                    if (isSelected) catColor else BorderColor
                                ),
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .clickable {
                                        currentCategory = catKey
                                        onUpdateCategory(catKey)
                                        Toast.makeText(context, "تم تحديث تصنيف العرض إلى $catLabel بنجاح ✅", Toast.LENGTH_SHORT).show()
                                        showCategoryDialog = false
                                    }
                            ) {
                                Row(
                                    modifier = Modifier.padding(horizontal = 12.dp, vertical = 10.dp),
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.SpaceBetween
                                ) {
                                    Text(
                                        text = catLabel,
                                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Normal,
                                        color = if (isSelected) Color.White else TextSecondary,
                                        fontSize = 13.sp
                                    )
                                    if (isSelected) {
                                        Icon(
                                            Icons.Default.Check,
                                            contentDescription = null,
                                            tint = catColor,
                                            modifier = Modifier.size(18.dp)
                                        )
                                    }
                                }
                            }
                        }
                    }
                },
                confirmButton = {},
                dismissButton = {
                    TextButton(onClick = { showCategoryDialog = false }) {
                        Text("إلغاء", color = TextSecondary)
                    }
                },
                containerColor = DarkSurface,
                titleContentColor = Color.White,
                textContentColor = TextSecondary
            )
        }

        // Hide Confirmation Dialog (Not Interested)
        if (showHideConfirmation) {
            AlertDialog(
                onDismissRequest = { showHideConfirmation = false },
                title = {
                    Text(
                        text = "إخفاء هذا العرض؟",
                        fontWeight = FontWeight.Bold,
                        style = MaterialTheme.typography.titleMedium
                    )
                },
                text = {
                    Text(
                        text = "لن يظهر لك \"${content.titleAr}\" مجدداً في البث المباشر أو جدول التالي أو البحث.",
                        fontSize = 13.sp,
                        color = TextSecondary
                    )
                },
                confirmButton = {
                    Button(
                        onClick = {
                            showHideConfirmation = false
                            onHideShow(content.titleAr)
                            Toast.makeText(context, "تم إخفاء العرض ولن يظهر لك مجدداً", Toast.LENGTH_SHORT).show()
                            onBackClick()
                        },
                        colors = ButtonDefaults.buttonColors(containerColor = PrimaryRed)
                    ) {
                        Text("إخفاء العرض", color = Color.White)
                    }
                },
                dismissButton = {
                    TextButton(onClick = { showHideConfirmation = false }) {
                        Text("إلغاء", color = TextSecondary)
                    }
                },
                containerColor = DarkSurface,
                titleContentColor = Color.White,
                textContentColor = TextSecondary
            )
        }
    }
}

@Composable
fun AiringCardItemWithPermission(
    airing: Airing,
    movieTitle: String,
    refreshKey: Int,
    onRemindClick: () -> Unit,
    onClick: () -> Unit
) {
    val context = LocalContext.current
    var isReminderSet by remember(airing.broadcastId, refreshKey) {
        mutableStateOf(ReminderManager.isReminderSet(context, airing.broadcastId))
    }

    Card(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick),
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = DarkSurface)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Row(
                verticalAlignment = Alignment.CenterVertically,
                modifier = Modifier.weight(1f)
            ) {
                Box(
                    modifier = Modifier
                        .size(40.dp)
                        .background(DarkSurfaceVariant, CircleShape)
                        .padding(6.dp),
                    contentAlignment = Alignment.Center
                ) {
                    AsyncImage(
                        model = airing.channelLogo,
                        contentDescription = airing.channelName,
                        modifier = Modifier.fillMaxSize(),
                        contentScale = ContentScale.Fit
                    )
                }
                Spacer(modifier = Modifier.width(12.dp))
                Column {
                    Text(
                        text = airing.channelName,
                        style = MaterialTheme.typography.bodyLarge,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Text(
                        text = "${airing.date} • الساعة ${airing.startTime}",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary
                    )
                }
            }

            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                // Remind Me Button
                Button(
                    onClick = onRemindClick,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = if (isReminderSet) AccentCyan.copy(alpha = 0.2f) else PrimaryRed.copy(alpha = 0.15f)
                    ),
                    shape = RoundedCornerShape(8.dp),
                    contentPadding = PaddingValues(horizontal = 10.dp, vertical = 6.dp)
                ) {
                    Icon(
                        imageVector = if (isReminderSet) Icons.Default.NotificationsActive else Icons.Default.NotificationsNone,
                        contentDescription = null,
                        tint = if (isReminderSet) AccentCyan else PrimaryRed,
                        modifier = Modifier.size(16.dp)
                    )
                    Spacer(modifier = Modifier.width(4.dp))
                    Text(
                        text = if (isReminderSet) "مفعّل" else "ذكّرني",
                        color = if (isReminderSet) AccentCyan else PrimaryRed,
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
        }
    }
}

@Composable
fun CastMemberItem(actor: CastMember) {
    Column(
        horizontalAlignment = Alignment.CenterHorizontally,
        modifier = Modifier.width(85.dp)
    ) {
        Box(
            modifier = Modifier
                .size(70.dp)
                .clip(CircleShape)
                .background(DarkSurfaceVariant),
            contentAlignment = Alignment.Center
        ) {
            if (!actor.profileUrl.isNullOrBlank()) {
                AsyncImage(
                    model = actor.profileUrl,
                    contentDescription = actor.name,
                    modifier = Modifier.fillMaxSize(),
                    contentScale = ContentScale.Crop
                )
            } else {
                Icon(
                    imageVector = Icons.Default.Person,
                    contentDescription = null,
                    tint = TextSecondary,
                    modifier = Modifier.size(36.dp)
                )
            }
        }
        Spacer(modifier = Modifier.height(6.dp))
        Text(
            text = actor.name,
            style = MaterialTheme.typography.labelSmall,
            fontWeight = FontWeight.Bold,
            color = Color.White,
            maxLines = 1
        )
        if (!actor.character.isNullOrEmpty()) {
            Text(
                text = actor.character,
                style = MaterialTheme.typography.labelSmall,
                color = AccentGold,
                fontSize = 10.sp,
                maxLines = 1
            )
        }
    }
}
