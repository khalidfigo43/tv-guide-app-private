package com.tvguide.app.ui.screens

import android.content.Context
import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.pager.HorizontalPager
import androidx.compose.foundation.pager.rememberPagerState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowForward
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tvguide.app.ui.theme.*
import kotlinx.coroutines.launch

data class OnboardingStep(
    val title: String,
    val subtitle: String,
    val description: String,
    val icon: ImageVector,
    val badgeText: String,
    val badgeColor: Color,
    val features: List<Pair<String, ImageVector>>
)

object OnboardingPrefs {
    private const val PREFS_NAME = "tvguide_user_prefs"
    private const val KEY_ONBOARDING_COMPLETED = "has_completed_onboarding_v1"

    fun isOnboardingCompleted(context: Context): Boolean {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getBoolean(KEY_ONBOARDING_COMPLETED, false)
    }

    fun setOnboardingCompleted(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putBoolean(KEY_ONBOARDING_COMPLETED, true).apply()
    }
}

@Composable
fun OnboardingScreen(
    onFinished: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()

    val steps = remember {
        listOf(
            OnboardingStep(
                title = "ماذا يُعرض الآن في التلفزيون؟ 📺",
                subtitle = "دليل برامج البث الحي والمباشر",
                description = "تابع كل ما يُبث في هذه اللحظة على أكثر من 250 قناة عربية وفضائية مع شريط الوقت المتبقي لكل عرض بدقة.",
                icon = Icons.Default.LiveTv,
                badgeText = "🔴 مباشر الآن",
                badgeColor = PrimaryRed,
                features = listOf(
                    "متابعة البث الحي لحظة بلحظة" to Icons.Default.PlayCircle,
                    "شريط التقدم والوقت المتبقي لكل عمل" to Icons.Default.Timer,
                    "صفحة جدول البث الكامل لكل قناة" to Icons.Default.CalendarMonth
                )
            ),
            OnboardingStep(
                title = "فرز وتصنيف ذكي 100% 🎬",
                subtitle = "أفلام، مسلسلات، رياضة ووثائقيات",
                description = "تصفح العروض والأفلام بدقة تامة. شاهد تفاصيل قصة العمل، طاقم الممثلين، وقنوات ومواعيد العرض القادمة.",
                icon = Icons.Default.Movie,
                badgeText = "✨ فئات نقية",
                badgeColor = AccentCyan,
                features = listOf(
                    "قسم مستقل للأفلام والمسلسلات والوثائقيات" to Icons.Default.LocalMovies,
                    "طاقم العمل والتمثيل مع صور الممثلين" to Icons.Default.Groups,
                    "بحث فوري بالاسم أو القناة أو الممثل" to Icons.Default.Search
                )
            ),
            OnboardingStep(
                title = "نظام التذكيرات الذكي ⏰",
                subtitle = "لا تفوت برامجك ومسلسلاتك المفضلة",
                description = "اضغط على «ذكّرني» في أي برنامج ليقوم التطبيق بجدولة إشعارات دقيقة قبل بدء العرض بالخيارات التي تفضلها.",
                icon = Icons.Default.NotificationsActive,
                badgeText = "🔔 تنبيهات مسبقة",
                badgeColor = AccentGold,
                features = listOf(
                    "تنبيه مبكر قبل موعد العرض بساعة" to Icons.Default.Alarm,
                    "تنبيه استعداد قبل بدء العرض بـ 10 دقائق" to Icons.Default.HourglassTop,
                    "إشعار فوري عند بدء العرض على القناة" to Icons.Default.Tv
                )
            ),
            OnboardingStep(
                title = "ضبط التوقيت والتحكم الكامل 🌍",
                subtitle = "حسب موقعك وتفضيلاتك الشخصية",
                description = "يضبط التطبيق مواعيد العروض تلقائياً بحسب دولتك، مع إمكانية إظهار أو إخفاء القنوات المشفرة والمدفوعة بنقرة واحدة.",
                icon = Icons.Default.Public,
                badgeText = "📍 توقيت محلي",
                badgeColor = Color(0xFF10B981),
                features = listOf(
                    "تحديد تلقائي لتوقيت دولتك أو اختيار بلدك" to Icons.Default.LocationOn,
                    "زر لإخفاء أو إظهار القنوات المشفرة (OSN)" to Icons.Default.Lock,
                    "تحديثات تلقائية للبيانات والنسخ الجديدة" to Icons.Default.SystemUpdate
                )
            )
        )
    }

    val pagerState = rememberPagerState(pageCount = { steps.size })

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    colors = listOf(DarkBackground, DarkSurface)
                )
            )
            .systemBarsPadding()
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(20.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            // Top Bar with Skip Button
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                // Step Indicator Pills
                Row(
                    horizontalArrangement = Arrangement.spacedBy(6.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    repeat(steps.size) { index ->
                        val isSelected = pagerState.currentPage == index
                        Box(
                            modifier = Modifier
                                .height(6.dp)
                                .width(if (isSelected) 24.dp else 8.dp)
                                .clip(CircleShape)
                                .background(if (isSelected) PrimaryRed else DarkSurfaceVariant)
                        )
                    }
                }

                TextButton(
                    onClick = {
                        OnboardingPrefs.setOnboardingCompleted(context)
                        onFinished()
                    }
                ) {
                    Text(
                        text = "تخطي",
                        color = TextSecondary,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )
                }
            }

            // Pager Content
            HorizontalPager(
                state = pagerState,
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth()
            ) { page ->
                val step = steps[page]
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 8.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    // Big Icon Box with glowing background
                    Box(
                        modifier = Modifier
                            .size(110.dp)
                            .background(step.badgeColor.copy(alpha = 0.15f), CircleShape)
                            .padding(20.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Icon(
                            imageVector = step.icon,
                            contentDescription = null,
                            tint = step.badgeColor,
                            modifier = Modifier.size(56.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(20.dp))

                    // Badge
                    Surface(
                        color = step.badgeColor.copy(alpha = 0.2f),
                        shape = RoundedCornerShape(20.dp)
                    ) {
                        Text(
                            text = step.badgeText,
                            color = step.badgeColor,
                            fontSize = 12.sp,
                            fontWeight = FontWeight.Bold,
                            modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp)
                        )
                    }

                    Spacer(modifier = Modifier.height(16.dp))

                    // Title
                    Text(
                        text = step.title,
                        color = Color.White,
                        fontSize = 22.sp,
                        fontWeight = FontWeight.Bold,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(6.dp))

                    // Subtitle
                    Text(
                        text = step.subtitle,
                        color = AccentGold,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(12.dp))

                    // Description
                    Text(
                        text = step.description,
                        color = TextSecondary,
                        fontSize = 13.sp,
                        lineHeight = 22.sp,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.padding(horizontal = 12.dp)
                    )

                    Spacer(modifier = Modifier.height(24.dp))

                    // Features Card
                    Surface(
                        color = DarkSurfaceVariant,
                        shape = RoundedCornerShape(16.dp),
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Column(
                            modifier = Modifier.padding(16.dp),
                            verticalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            step.features.forEach { (text, icon) ->
                                Row(
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Box(
                                        modifier = Modifier
                                            .size(28.dp)
                                            .background(step.badgeColor.copy(alpha = 0.2f), CircleShape),
                                        contentAlignment = Alignment.Center
                                    ) {
                                        Icon(
                                            imageVector = icon,
                                            contentDescription = null,
                                            tint = step.badgeColor,
                                            modifier = Modifier.size(16.dp)
                                        )
                                    }
                                    Spacer(modifier = Modifier.width(12.dp))
                                    Text(
                                        text = text,
                                        color = Color.White,
                                        fontSize = 13.sp,
                                        fontWeight = FontWeight.Medium
                                    )
                                }
                            }
                        }
                    }
                }
            }

            // Bottom Buttons
            val isLastPage = pagerState.currentPage == steps.size - 1

            Button(
                onClick = {
                    if (isLastPage) {
                        OnboardingPrefs.setOnboardingCompleted(context)
                        onFinished()
                    } else {
                        scope.launch {
                            pagerState.animateScrollToPage(pagerState.currentPage + 1)
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(52.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryRed)
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.Center
                ) {
                    Text(
                        text = if (isLastPage) "ابدأ الاستخدام الآن 🚀" else "التالي",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color.White
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Icon(
                        imageVector = if (isLastPage) Icons.Default.CheckCircle else Icons.AutoMirrored.Filled.ArrowForward,
                        contentDescription = null,
                        tint = Color.White,
                        modifier = Modifier.size(20.dp)
                    )
                }
            }
        }
    }
}
