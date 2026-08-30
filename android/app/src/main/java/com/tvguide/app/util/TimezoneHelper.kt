package com.tvguide.app.util

import java.util.Locale
import java.util.TimeZone

data class AppCountryTimezone(
    val id: String,
    val countryNameAr: String,
    val flag: String,
    val defaultOffsetHoursFromKsa: Int,
    val isAuto: Boolean = false
)

object TimezoneHelper {

    val supportedCountries = listOf(
        AppCountryTimezone(
            id = "AUTO",
            countryNameAr = "تحديد تلقائي (حسب موقع وتوقيت هاتفك)",
            flag = "📍",
            defaultOffsetHoursFromKsa = 0,
            isAuto = true
        ),
        AppCountryTimezone(
            id = "EG",
            countryNameAr = "مصر (توقيت القاهرة)",
            flag = "🇪🇬",
            defaultOffsetHoursFromKsa = getEgyptOffsetFromKsa()
        ),
        AppCountryTimezone(
            id = "SA",
            countryNameAr = "المملكة العربية السعودية (توقيت مكة)",
            flag = "🇸🇦",
            defaultOffsetHoursFromKsa = 0
        ),
        AppCountryTimezone(
            id = "AE",
            countryNameAr = "الإمارات العربية المتحدة (توقيت دبي)",
            flag = "🇦🇪",
            defaultOffsetHoursFromKsa = 1
        ),
        AppCountryTimezone(
            id = "KW_QA_BH",
            countryNameAr = "الكويت، قطر، البحرين (توقيت الخليج)",
            flag = "🇰🇼 🇶🇦 🇧🇭",
            defaultOffsetHoursFromKsa = 0
        ),
        AppCountryTimezone(
            id = "IQ",
            countryNameAr = "العراق (توقيت بغداد)",
            flag = "🇮🇶",
            defaultOffsetHoursFromKsa = 0
        ),
        AppCountryTimezone(
            id = "LEVANT",
            countryNameAr = "الأردن، فلسطين، لبنان، سوريا",
            flag = "🇯🇴 🇵🇸 🇱🇧 🇸🇾",
            defaultOffsetHoursFromKsa = 0
        ),
        AppCountryTimezone(
            id = "SD_LY",
            countryNameAr = "السودان وليبيا (توقيت طرابلس والخرطوم)",
            flag = "🇸🇩 🇱🇾",
            defaultOffsetHoursFromKsa = -1
        ),
        AppCountryTimezone(
            id = "DZ_TN",
            countryNameAr = "الجزائر وتونس",
            flag = "🇩🇿 🇹🇳",
            defaultOffsetHoursFromKsa = -2
        ),
        AppCountryTimezone(
            id = "MA",
            countryNameAr = "المملكة المغربية (توقيت الرباط)",
            flag = "🇲🇦",
            defaultOffsetHoursFromKsa = -2
        ),
        AppCountryTimezone(
            id = "GMT",
            countryNameAr = "توقيت غرينتش العالمي (UTC)",
            flag = "🌍",
            defaultOffsetHoursFromKsa = -3
        )
    )

    fun getDeviceOffsetFromKsa(): Int {
        return try {
            val tz = TimeZone.getDefault()
            val now = System.currentTimeMillis()
            val deviceOffsetMs = tz.getOffset(now)
            val ksaOffsetMs = 3 * 3600 * 1000 // Base schedules are UTC+3 (KSA)
            ((deviceOffsetMs - ksaOffsetMs) / (3600 * 1000))
        } catch (e: Exception) {
            0
        }
    }

    private fun getEgyptOffsetFromKsa(): Int {
        return try {
            val tz = TimeZone.getTimeZone("Africa/Cairo")
            val now = System.currentTimeMillis()
            val cairoOffsetMs = tz.getOffset(now)
            val ksaOffsetMs = 3 * 3600 * 1000
            ((cairoOffsetMs - ksaOffsetMs) / (3600 * 1000))
        } catch (e: Exception) {
            0
        }
    }

    fun getEffectiveOffset(selected: AppCountryTimezone): Int {
        return if (selected.isAuto) {
            getDeviceOffsetFromKsa()
        } else {
            selected.defaultOffsetHoursFromKsa
        }
    }

    fun detectDefaultCountry(): AppCountryTimezone {
        return try {
            val countryCode = Locale.getDefault().country.uppercase()
            when (countryCode) {
                "EG" -> supportedCountries.first { it.id == "EG" }
                "SA" -> supportedCountries.first { it.id == "SA" }
                "AE" -> supportedCountries.first { it.id == "AE" }
                "KW", "QA", "BH" -> supportedCountries.first { it.id == "KW_QA_BH" }
                "IQ" -> supportedCountries.first { it.id == "IQ" }
                "JO", "PS", "LB", "SY" -> supportedCountries.first { it.id == "LEVANT" }
                "SD", "LY" -> supportedCountries.first { it.id == "SD_LY" }
                "DZ", "TN" -> supportedCountries.first { it.id == "DZ_TN" }
                "MA" -> supportedCountries.first { it.id == "MA" }
                else -> supportedCountries.first { it.id == "AUTO" }
            }
        } catch (e: Exception) {
            supportedCountries.first { it.id == "AUTO" }
        }
    }

    fun adjustTime(timeStr: String?, offsetHours: Int): String {
        if (timeStr.isNullOrBlank() || offsetHours == 0) return timeStr ?: "12:00"
        return try {
            val parts = timeStr.trim().split(":")
            if (parts.size < 2) return timeStr
            val h = parts[0].toIntOrNull() ?: 12
            val m = parts[1].toIntOrNull() ?: 0

            var adjustedH = (h + offsetHours) % 24
            if (adjustedH < 0) adjustedH += 24

            String.format("%02d:%02d", adjustedH, m)
        } catch (e: Exception) {
            timeStr
        }
    }
}
