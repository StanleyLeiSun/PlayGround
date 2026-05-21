package com.kidscheck.app.util

import android.app.DownloadManager
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.net.Uri
import android.os.Environment
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.AppVersion
import java.io.File

data class DownloadStatus(
    val status: Int,
    val progress: Int,
    val localUri: String?
)

object ApkDownloader {

    private var downloadId: Long = -1
    private var onComplete: ((String) -> Unit)? = null
    private var onProgress: ((Int) -> Unit)? = null

    private val downloadReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val id = intent.getLongExtra(DownloadManager.EXTRA_DOWNLOAD_ID, -1)
            if (id == downloadId) {
                val query = DownloadManager.Query().setFilterById(downloadId)
                val manager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                val cursor = manager.query(query)

                if (cursor.moveToFirst()) {
                    val statusIndex = cursor.getColumnIndex(DownloadManager.COLUMN_STATUS)
                    val status = cursor.getInt(statusIndex)

                    when (status) {
                        DownloadManager.STATUS_SUCCESSFUL -> {
                            val localUriIndex = cursor.getColumnIndex(DownloadManager.COLUMN_LOCAL_URI)
                            val localUri = cursor.getString(localUriIndex)
                            onComplete?.invoke(localUri)
                        }
                        DownloadManager.STATUS_FAILED -> {
                            onComplete?.invoke("")
                        }
                    }
                }
                cursor.close()
            }
        }
    }

    fun startDownload(context: Context, version: AppVersion): Long {
        val baseUrl = RetrofitInstance.BASE_URL
        val apkUrl = "$baseUrl${version.apkUrl}"

        val request = DownloadManager.Request(Uri.parse(apkUrl))
            .setTitle("KidsCheck 更新")
            .setDescription("正在下载版本 ${version.versionName}")
            .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
            .setDestinationInExternalPublicDir(
                Environment.DIRECTORY_DOWNLOADS,
                "kidscheck-${version.versionName}.apk"
            )
            .setAllowedOverMetered(true)
            .setAllowedOverRoaming(true)

        val manager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        downloadId = manager.enqueue(request)

        // 保存下载ID到SharedPreferences
        val prefs = context.getSharedPreferences("update_prefs", Context.MODE_PRIVATE)
        prefs.edit().putLong("download_id", downloadId).apply()

        return downloadId
    }

    fun getDownloadStatus(context: Context): DownloadStatus {
        if (downloadId == -1L) {
            return DownloadStatus(DownloadManager.STATUS_FAILED, 0, null)
        }

        val query = DownloadManager.Query().setFilterById(downloadId)
        val manager = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
        val cursor = manager.query(query)

        if (cursor.moveToFirst()) {
            val statusIndex = cursor.getColumnIndex(DownloadManager.COLUMN_STATUS)
            val progressIndex = cursor.getColumnIndex(DownloadManager.COLUMN_BYTES_DOWNLOADED_SO_FAR)
            val totalIndex = cursor.getColumnIndex(DownloadManager.COLUMN_TOTAL_SIZE_BYTES)
            val localUriIndex = cursor.getColumnIndex(DownloadManager.COLUMN_LOCAL_URI)

            val status = cursor.getInt(statusIndex)
            val progress = cursor.getInt(progressIndex)
            val total = cursor.getInt(totalIndex)
            val localUri = cursor.getString(localUriIndex)

            val progressPercent = if (total > 0) (progress * 100 / total) else 0

            cursor.close()
            return DownloadStatus(status, progressPercent, localUri)
        }

        cursor.close()
        return DownloadStatus(DownloadManager.STATUS_FAILED, 0, null)
    }

    fun registerReceiver(context: Context, onComplete: (String) -> Unit, onProgress: (Int) -> Unit) {
        this.onComplete = onComplete
        this.onProgress = onProgress

        val filter = IntentFilter(DownloadManager.ACTION_DOWNLOAD_COMPLETE)
        context.registerReceiver(downloadReceiver, filter)
    }

    fun unregisterReceiver(context: Context) {
        try {
            context.unregisterReceiver(downloadReceiver)
        } catch (e: Exception) {
            // Receiver not registered
        }
        onComplete = null
        onProgress = null
    }

    fun getDownloadId(): Long = downloadId

    fun setDownloadId(id: Long) {
        downloadId = id
    }
}
