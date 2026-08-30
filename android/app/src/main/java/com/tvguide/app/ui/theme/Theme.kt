package com.tvguide.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

// Modern TV Guide Dark Palette
val DarkBackground = Color(0xFF0F1015)
val DarkSurface = Color(0xFF181A22)
val DarkSurfaceVariant = Color(0xFF222531)
val PrimaryRed = Color(0xFFE50914) // Accent broadcast red
val AccentGold = Color(0xFFFFB800) // Star rating gold
val AccentCyan = Color(0xFF00D2FF) // Live broadcast highlight
val TextPrimary = Color(0xFFFFFFFF)
val TextSecondary = Color(0xFFA0A5B5)
val TextMuted = Color(0xFF6B7280)
val BorderColor = Color(0xFF2A2E3D)

private val DarkColorScheme = darkColorScheme(
    primary = PrimaryRed,
    secondary = AccentGold,
    tertiary = AccentCyan,
    background = DarkBackground,
    surface = DarkSurface,
    surfaceVariant = DarkSurfaceVariant,
    onPrimary = Color.White,
    onSecondary = Color.Black,
    onTertiary = Color.Black,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
    onSurfaceVariant = TextSecondary
)

@Composable
fun TVGuideTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        content = content
    )
}

