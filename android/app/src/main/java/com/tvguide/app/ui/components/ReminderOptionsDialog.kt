package com.tvguide.app.ui.components

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Alarm
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.NotificationsActive
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.tvguide.app.ui.theme.*
import com.tvguide.app.util.ReminderTimingOptions

@Composable
fun ReminderOptionsDialog(
    showTitle: String,
    channelName: String,
    startTime: String,
    onConfirm: (ReminderTimingOptions) -> Unit,
    onDismiss: () -> Unit
) {
    var remind1Hr by remember { mutableStateOf(true) }
    var remind10Min by remember { mutableStateOf(true) }
    var remindAtTime by remember { mutableStateOf(true) }

    AlertDialog(
        onDismissRequest = onDismiss,
        containerColor = DarkSurface,
        title = {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Icon(
                    imageVector = Icons.Default.NotificationsActive,
                    contentDescription = null,
                    tint = AccentGold,
                    modifier = Modifier.size(24.dp)
                )
                Spacer(modifier = Modifier.width(10.dp))
                Text(
                    text = "خيارات ضبط التذكير ⏰",
                    color = Color.White,
                    fontSize = 17.sp,
                    fontWeight = FontWeight.Bold
                )
            }
        },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Text(
                    text = "\"$showTitle\" على قناة $channelName (الساعة $startTime)",
                    color = AccentCyan,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    text = "حدد أوقات التنبيه التي ترغب في استلام إشعارات بها:",
                    color = TextSecondary,
                    fontSize = 12.sp
                )
                Spacer(modifier = Modifier.height(4.dp))

                // Option 1: 1 Hour Before
                Surface(
                    color = if (remind1Hr) AccentCyan.copy(alpha = 0.15f) else DarkSurfaceVariant,
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { remind1Hr = !remind1Hr }
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(
                                checked = remind1Hr,
                                onCheckedChange = { remind1Hr = it },
                                colors = CheckboxDefaults.colors(checkedColor = AccentCyan)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "⏰ قبل بدء العرض بـ 1 ساعة",
                                color = if (remind1Hr) Color.White else TextSecondary,
                                fontWeight = if (remind1Hr) FontWeight.Bold else FontWeight.Normal,
                                fontSize = 13.sp
                            )
                        }
                    }
                }

                // Option 2: 10 Minutes Before
                Surface(
                    color = if (remind10Min) AccentCyan.copy(alpha = 0.15f) else DarkSurfaceVariant,
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { remind10Min = !remind10Min }
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(
                                checked = remind10Min,
                                onCheckedChange = { remind10Min = it },
                                colors = CheckboxDefaults.colors(checkedColor = AccentCyan)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "⏳ قبل بدء العرض بـ 10 دقائق",
                                color = if (remind10Min) Color.White else TextSecondary,
                                fontWeight = if (remind10Min) FontWeight.Bold else FontWeight.Normal,
                                fontSize = 13.sp
                            )
                        }
                    }
                }

                // Option 3: At Showtime
                Surface(
                    color = if (remindAtTime) AccentCyan.copy(alpha = 0.15f) else DarkSurfaceVariant,
                    shape = RoundedCornerShape(10.dp),
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable { remindAtTime = !remindAtTime }
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Checkbox(
                                checked = remindAtTime,
                                onCheckedChange = { remindAtTime = it },
                                colors = CheckboxDefaults.colors(checkedColor = AccentCyan)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = "🎬 عند موعد بدء العرض مباشرة",
                                color = if (remindAtTime) Color.White else TextSecondary,
                                fontWeight = if (remindAtTime) FontWeight.Bold else FontWeight.Normal,
                                fontSize = 13.sp
                            )
                        }
                    }
                }
            }
        },
        confirmButton = {
            Button(
                onClick = {
                    onConfirm(
                        ReminderTimingOptions(
                            remind1HourBefore = remind1Hr,
                            remind10MinBefore = remind10Min,
                            remindAtShowTime = remindAtTime
                        )
                    )
                },
                colors = ButtonDefaults.buttonColors(containerColor = PrimaryRed),
                shape = RoundedCornerShape(8.dp)
            ) {
                Text("تأكيد التذكير", color = Color.White, fontWeight = FontWeight.Bold)
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("إلغاء", color = TextSecondary)
            }
        }
    )
}

