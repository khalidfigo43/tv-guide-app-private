package com.tvguide.app.util

import android.Manifest
import android.app.AlarmManager
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.widget.Toast
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat
import com.tvguide.app.MainActivity
import java.util.*

class ReminderReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        val title = intent.getStringExtra("EXTRA_TITLE") ?: "برنامج تلفزيوني"
        val channelName = intent.getStringExtra("EXTRA_CHANNEL") ?: "قناة فضائية"
        val startTime = intent.getStringExtra("EXTRA_TIME") ?: ""
        val notifMessage = intent.getStringExtra("EXTRA_MSG") ?: "حان موعد عرض: $title على قناة $channelName"
        val requestCode = intent.getIntExtra("EXTRA_CODE", title.hashCode())

        val notificationManager = context.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
        val channelId = "tv_guide_reminders"

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "تنبيهات مواعيد البرامج والأفلام",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "إشعارات تذكيرية قبل بدء البرامج والأفلام المفضلة"
                enableVibration(true)
            }
            notificationManager.createNotificationChannel(channel)
        }

        val openAppIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            context,
            requestCode,
            openAppIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, channelId)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle("🎬 دليل التلفزيون: $title")
            .setContentText(notifMessage)
            .setStyle(
                NotificationCompat.BigTextStyle()
                    .bigText("$notifMessage\nالموعد: الساعة $startTime على قناة $channelName. نتمنى لك مشاهدة ممتعة!")
            )
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        notificationManager.notify(requestCode, notification)
    }
}

data class ReminderTimingOptions(
    val remind1HourBefore: Boolean = true,
    val remind10MinBefore: Boolean = true,
    val remindAtShowTime: Boolean = true
)

object ReminderManager {
    private const val PREFS_NAME = "tv_guide_reminders_prefs"

    fun hasNotificationPermission(context: Context): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    fun isReminderSet(context: Context, broadcastId: Long): Boolean {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        return prefs.getBoolean("rem_$broadcastId", false)
    }

    fun cancelReminder(context: Context, broadcastId: Long, title: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager

        // Cancel all 3 sub-alarms
        listOf(1, 2, 3).forEach { offsetType ->
            val code = (broadcastId.toInt() * 10) + offsetType
            val intent = Intent(context, ReminderReceiver::class.java)
            val pi = PendingIntent.getBroadcast(
                context,
                code,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            alarmManager.cancel(pi)
        }

        prefs.edit().putBoolean("rem_$broadcastId", false).apply()
        Toast.makeText(context, "تم إلغاء التذكير لـ $title", Toast.LENGTH_SHORT).show()
    }

    fun setReminder(
        context: Context,
        broadcastId: Long,
        title: String,
        channelName: String,
        startTime: String,
        options: ReminderTimingOptions = ReminderTimingOptions()
    ): Boolean {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val alarmManager = context.getSystemService(Context.ALARM_SERVICE) as AlarmManager

        try {
            val cal = Calendar.getInstance()
            val parts = startTime.split(":")
            if (parts.size >= 2) {
                val h = parts[0].toIntOrNull() ?: 12
                val m = parts[1].toIntOrNull() ?: 0
                cal.set(Calendar.HOUR_OF_DAY, h)
                cal.set(Calendar.MINUTE, m)
                cal.set(Calendar.SECOND, 0)

                // If show time has passed today, schedule for tomorrow
                if (cal.timeInMillis < System.currentTimeMillis()) {
                    cal.add(Calendar.DAY_OF_YEAR, 1)
                }

                val showTimeMillis = cal.timeInMillis
                val now = System.currentTimeMillis()

                // 1. Alert 1 Hour Before
                if (options.remind1HourBefore) {
                    val alert1Hr = showTimeMillis - (60 * 60 * 1000)
                    if (alert1Hr > now) {
                        val code = (broadcastId.toInt() * 10) + 1
                        val intent = Intent(context, ReminderReceiver::class.java).apply {
                            putExtra("EXTRA_TITLE", title)
                            putExtra("EXTRA_CHANNEL", channelName)
                            putExtra("EXTRA_TIME", startTime)
                            putExtra("EXTRA_MSG", "⏰ تذكير: يبدأ بعد ساعة عرض \"$title\" على قناة $channelName")
                            putExtra("EXTRA_CODE", code)
                        }
                        val pi = PendingIntent.getBroadcast(context, code, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                        scheduleAlarm(alarmManager, alert1Hr, pi)
                    }
                }

                // 2. Alert 10 Minutes Before
                if (options.remind10MinBefore) {
                    val alert10Min = showTimeMillis - (10 * 60 * 1000)
                    if (alert10Min > now) {
                        val code = (broadcastId.toInt() * 10) + 2
                        val intent = Intent(context, ReminderReceiver::class.java).apply {
                            putExtra("EXTRA_TITLE", title)
                            putExtra("EXTRA_CHANNEL", channelName)
                            putExtra("EXTRA_TIME", startTime)
                            putExtra("EXTRA_MSG", "⏳ اقترب الموعد: يبدأ بعد 10 دقائق عرض \"$title\" على قناة $channelName")
                            putExtra("EXTRA_CODE", code)
                        }
                        val pi = PendingIntent.getBroadcast(context, code, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                        scheduleAlarm(alarmManager, alert10Min, pi)
                    }
                }

                // 3. Alert At Showtime
                if (options.remindAtShowTime) {
                    val code = (broadcastId.toInt() * 10) + 3
                    val intent = Intent(context, ReminderReceiver::class.java).apply {
                        putExtra("EXTRA_TITLE", title)
                        putExtra("EXTRA_CHANNEL", channelName)
                        putExtra("EXTRA_TIME", startTime)
                        putExtra("EXTRA_MSG", "🎬 يبدأ الآن عرض \"$title\" على قناة $channelName")
                        putExtra("EXTRA_CODE", code)
                    }
                    val pi = PendingIntent.getBroadcast(context, code, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
                    scheduleAlarm(alarmManager, showTimeMillis, pi)
                }

                prefs.edit().putBoolean("rem_$broadcastId", true).apply()
                Toast.makeText(
                    context,
                    "🔔 تم ضبط تذكير \"$title\" (قبل العرض بساعة، و 10 دقائق، وعند البدء) بنجاح!",
                    Toast.LENGTH_LONG
                ).show()
                return true
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return false
    }

    private fun scheduleAlarm(alarmManager: AlarmManager, timeMillis: Long, pendingIntent: PendingIntent) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            alarmManager.setExactAndAllowWhileIdle(AlarmManager.RTC_WAKEUP, timeMillis, pendingIntent)
        } else {
            alarmManager.setExact(AlarmManager.RTC_WAKEUP, timeMillis, pendingIntent)
        }
    }
}
