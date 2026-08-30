package com.tvguide.app.util

import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.widget.Toast
import androidx.core.content.FileProvider
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import okhttp3.OkHttpClient
import okhttp3.Request
import java.io.File
import java.io.FileOutputStream
import java.util.concurrent.TimeUnit

@Serializable
data class AppUpdateInfo(
    @SerialName("version_code") val versionCode: Int = 1,
    @SerialName("version_name") val versionName: String = "1.0.0",
    @SerialName("apk_url") val apkUrl: String = "",
    @SerialName("release_notes") val releaseNotes: String = "",
    @SerialName("is_force_update") val isForceUpdate: Boolean = false,
    @SerialName("publish_date") val publishDate: String = ""
)

object UpdateManager {
    // Primary public update endpoint on GitHub
    var updateEndpointUrl = "https://raw.githubusercontent.com/khalidfigo43/tv-guide-releases/main/version.json"

    private val httpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    private val json = Json { ignoreUnknownKeys = true; isLenient = true }

    suspend fun checkForUpdate(currentVersionCode: Int): AppUpdateInfo? = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url(updateEndpointUrl)
                .addHeader("Cache-Control", "no-cache")
                .build()

            httpClient.newCall(request).execute().use { response ->
                if (!response.isSuccessful) return@withContext null
                val bodyStr = response.body?.string() ?: return@withContext null
                val info = json.decodeFromString<AppUpdateInfo>(bodyStr)
                if (info.versionCode > currentVersionCode && info.apkUrl.isNotBlank()) {
                    return@withContext info
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return@withContext null
    }

    suspend fun downloadAndInstallApk(
        context: Context,
        apkUrl: String,
        versionName: String,
        onProgress: (Float) -> Unit,
        onComplete: () -> Unit,
        onError: (String) -> Unit
    ) = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder().url(apkUrl).build()
            httpClient.newCall(request).execute().use { response ->
                if (!response.isSuccessful) {
                    withContext(Dispatchers.Main) {
                        onError("فشل تحميل التحديث (كود الاستجابة: ${response.code})")
                    }
                    return@withContext
                }

                val body = response.body ?: run {
                    withContext(Dispatchers.Main) { onError("الملف فارغ") }
                    return@withContext
                }

                val totalLength = body.contentLength()
                val destDir = File(context.cacheDir, "updates").apply { if (!exists()) mkdirs() }
                val apkFile = File(destDir, "TVGuide-v$versionName.apk")

                val input = body.byteStream()
                val output = FileOutputStream(apkFile)
                val buffer = ByteArray(8 * 1024)
                var bytesRead: Int
                var totalRead = 0L

                while (input.read(buffer).also { bytesRead = it } != -1) {
                    output.write(buffer, 0, bytesRead)
                    totalRead += bytesRead
                    if (totalLength > 0) {
                        val progress = totalRead.toFloat() / totalLength.toFloat()
                        withContext(Dispatchers.Main) {
                            onProgress(progress)
                        }
                    }
                }

                output.flush()
                output.close()
                input.close()

                withContext(Dispatchers.Main) {
                    onComplete()
                    installApk(context, apkFile)
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
            withContext(Dispatchers.Main) {
                onError("خطأ أثناء تحميل التحديث: ${e.localizedMessage}")
            }
        }
    }

    fun installApk(context: Context, apkFile: File) {
        try {
            if (!apkFile.exists()) {
                Toast.makeText(context, "ملف التحديث غير موجود", Toast.LENGTH_SHORT).show()
                return
            }

            val uri: Uri = FileProvider.getUriForFile(
                context,
                "${context.packageName}.fileprovider",
                apkFile
            )

            val intent = Intent(Intent.ACTION_VIEW).apply {
                setDataAndType(uri, "application/vnd.android.package-archive")
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_GRANT_READ_URI_PERMISSION
            }
            context.startActivity(intent)
        } catch (e: Exception) {
            e.printStackTrace()
            Toast.makeText(context, "تعذر فتح ملف التثبيت: ${e.localizedMessage}", Toast.LENGTH_LONG).show()
        }
    }
}

