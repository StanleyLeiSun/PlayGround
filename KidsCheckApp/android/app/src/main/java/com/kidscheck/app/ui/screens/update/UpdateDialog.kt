package com.kidscheck.app.ui.screens.update

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kidscheck.app.data.model.AppVersion
import com.kidscheck.app.ui.theme.*

@Composable
fun UpdateDialog(
    version: AppVersion,
    isDownloading: Boolean,
    downloadProgress: Int,
    onUpdateClick: () -> Unit,
    onSkipClick: (() -> Unit)?,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = { if (!isDownloading && onSkipClick != null) onDismiss() },
        title = {
            Text(
                text = "发现新版本",
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
        },
        text = {
            Column {
                Text(
                    text = "版本 ${version.versionName}",
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Medium,
                    color = Primary
                )

                Spacer(modifier = Modifier.height(8.dp))

                Text(
                    text = "更新内容：",
                    fontSize = 14.sp,
                    fontWeight = FontWeight.Medium
                )

                Spacer(modifier = Modifier.height(4.dp))

                Text(
                    text = version.releaseNotes,
                    fontSize = 14.sp,
                    color = TextSecondary
                )

                if (version.apkSize > 0) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = "大小：${formatFileSize(version.apkSize)}",
                        fontSize = 12.sp,
                        color = TextSecondary
                    )
                }

                if (isDownloading) {
                    Spacer(modifier = Modifier.height(16.dp))
                    LinearProgressIndicator(
                        progress = downloadProgress / 100f,
                        modifier = Modifier.fillMaxWidth(),
                        color = Primary
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        text = "下载中... $downloadProgress%",
                        fontSize = 12.sp,
                        color = TextSecondary,
                        modifier = Modifier.align(Alignment.CenterHorizontally)
                    )
                }
            }
        },
        confirmButton = {
            Button(
                onClick = onUpdateClick,
                enabled = !isDownloading,
                colors = ButtonDefaults.buttonColors(containerColor = Primary)
            ) {
                Text(
                    text = if (isDownloading) "下载中..." else "立即更新",
                    fontWeight = FontWeight.SemiBold
                )
            }
        },
        dismissButton = {
            if (onSkipClick != null && !isDownloading) {
                TextButton(onClick = onSkipClick) {
                    Text(
                        text = "稍后再说",
                        color = TextSecondary
                    )
                }
            }
        },
        shape = RoundedCornerShape(16.dp)
    )
}

private fun formatFileSize(bytes: Long): String {
    return when {
        bytes >= 1024 * 1024 -> "${bytes / (1024 * 1024)} MB"
        bytes >= 1024 -> "${bytes / 1024} KB"
        else -> "$bytes B"
    }
}
