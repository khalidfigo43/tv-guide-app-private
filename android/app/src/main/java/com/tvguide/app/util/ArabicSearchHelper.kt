package com.tvguide.app.util

object ArabicSearchHelper {

    /**
     * Normalizes Arabic text by unifying letters with various forms (hamza, ta marbuta, etc.)
     * and removing all diacritics / tashkeel for resilient approximate searching.
     */
    fun normalizeArabic(input: String?): String {
        if (input.isNullOrBlank()) return ""
        
        var text = input.trim().lowercase()

        // 1. Remove Tashkeel / Harakat (Fatha, Damma, Kasra, Sukun, Tanwin, Shadda, etc.)
        text = text.replace(Regex("[\\u064B-\\u065F\\u0670]"), "")

        // 2. Remove Tatweel (Kashida)
        text = text.replace("\u0640", "")

        // 3. Normalize Alef forms (أ, إ, آ, ٱ -> ا)
        text = text.replace(Regex("[أإآٱ]"), "ا")

        // 4. Normalize Ta Marbuta (ة -> ه)
        text = text.replace("ة", "ه")

        // 5. Normalize Ya and Alef Maqsura (ى, ئ -> ي)
        text = text.replace(Regex("[ىئ]"), "ي")

        // 6. Normalize Waw with Hamza (ؤ -> و)
        text = text.replace("ؤ", "و")

        // 7. Normalize Persian/Urdu variants (گ -> ك, پ -> ب, ڤ -> ف, ژ -> ز)
        text = text.replace("گ", "ك")
            .replace("پ", "ب")
            .replace("ڤ", "ف")
            .replace("ژ", "ز")

        // 8. Normalize punctuation and multiple spaces
        text = text.replace(Regex("[\\p{Punct}\\s]+"), " ")

        return text.trim()
    }

    /**
     * Checks if the normalized target contains the normalized query.
     */
    fun matches(target: String?, query: String?): Boolean {
        if (query.isNullOrBlank()) return true
        if (target.isNullOrBlank()) return false
        val normTarget = normalizeArabic(target)
        val normQuery = normalizeArabic(query)
        return normTarget.contains(normQuery)
    }

    /**
     * Returns true if the string contains Arabic characters.
     */
    fun isArabicText(input: String?): Boolean {
        if (input.isNullOrBlank()) return false
        return input.any { it in '\u0600'..'\u06FF' || it in '\u0750'..'\u077F' }
    }
}

