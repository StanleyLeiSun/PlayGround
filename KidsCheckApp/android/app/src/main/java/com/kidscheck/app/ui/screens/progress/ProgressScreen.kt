package com.kidscheck.app.ui.screens.progress

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.DailyTask
import com.kidscheck.app.data.model.ProgressResponse
import com.kidscheck.app.ui.theme.*
import java.time.LocalDate
import java.time.LocalDateTime
import java.time.OffsetDateTime
import java.time.ZoneId
import java.time.ZoneOffset
import java.time.format.DateTimeParseException
import java.time.format.DateTimeFormatter
import kotlinx.coroutines.launch

@Composable
fun ProgressScreen(childId: Int) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var progress by remember { mutableStateOf<ProgressResponse?>(null) }
    var currentDate by remember { mutableStateOf(LocalDate.now()) }
    var loading by remember { mutableStateOf(true) }
    var photoViewerUrls by remember { mutableStateOf<List<String>>(emptyList()) }
    var photoViewerIndex by remember { mutableIntStateOf(0) }
    var showPhotoViewer by remember { mutableStateOf(false) }

    LaunchedEffect(childId, currentDate) {
        loading = true
        scope.launch {
            try {
                val dateStr = currentDate.format(DateTimeFormatter.ISO_LOCAL_DATE)
                val resp = RetrofitInstance.getApi(context).getProgress(childId, dateStr)
                if (resp.isSuccessful) progress = resp.body()
            } catch (_: Exception) {}
            loading = false
        }
    }

    if (loading) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator(color = Primary, modifier = Modifier.semantics { contentDescription = "progress_loading" })
        }
        return
    }

    val p = progress ?: return
    val timelineTasks = remember(p.tasks) {
        p.tasks.sortedWith(compareBy<DailyTask> { it.isConditional }.thenBy { it.completedAt ?: "zzz" })
    }

    if (showPhotoViewer) {
        AlertDialog(
            onDismissRequest = { showPhotoViewer = false },
            confirmButton = { TextButton(onClick = { showPhotoViewer = false }) { Text("关闭") } },
            title = { Text("照片") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    val url = photoViewerUrls.getOrNull(photoViewerIndex)
                    if (url != null) {
                        AsyncImage(
                            model = url,
                            contentDescription = null,
                            modifier = Modifier.fillMaxWidth().height(320.dp).clip(RoundedCornerShape(12.dp)),
                            contentScale = ContentScale.Crop
                        )
                        if (photoViewerUrls.size > 1) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                TextButton(
                                    onClick = { photoViewerIndex = (photoViewerIndex - 1).coerceAtLeast(0) },
                                    enabled = photoViewerIndex > 0
                                ) { Text("上一张") }
                                Text("${photoViewerIndex + 1}/${photoViewerUrls.size}", color = TextSecondary)
                                TextButton(
                                    onClick = { photoViewerIndex = (photoViewerIndex + 1).coerceAtMost(photoViewerUrls.size - 1) },
                                    enabled = photoViewerIndex < photoViewerUrls.size - 1
                                ) { Text("下一张") }
                            }
                        }
                    } else {
                        Text("无法加载照片链接", color = TextSecondary)
                    }
                }
            }
        )
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Date navigation
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = { currentDate = currentDate.minusDays(1) }, modifier = Modifier.semantics { contentDescription = "progress_prev_day" }) {
                    Icon(Icons.Default.ChevronLeft, "上一天")
                }
                Text(
                    "${currentDate.monthValue}月${currentDate.dayOfMonth}日",
                    fontSize = 16.sp, fontWeight = FontWeight.SemiBold
                )
                IconButton(onClick = { currentDate = currentDate.plusDays(1) }, modifier = Modifier.semantics { contentDescription = "progress_next_day" }) {
                    Icon(Icons.Default.ChevronRight, "下一天")
                }
            }
        }

        // Progress bar
        item {
            Surface(shape = RoundedCornerShape(16.dp), color = GrayLight) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("完成进度", fontSize = 14.sp, color = TextSecondary)
                        Text("${p.completedTasks}/${p.totalTasks}", fontSize = 14.sp, color = TextSecondary)
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    LinearProgressIndicator(
                        progress = if (p.totalTasks > 0) p.completedTasks.toFloat() / p.totalTasks else 0f,
                        modifier = Modifier.fillMaxWidth().height(12.dp).clip(RoundedCornerShape(6.dp)),
                        color = Primary,
                        trackColor = Border,
                    )
                }
            }
        }

        // Timeline
        item {
            Text("📅 时间线", fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = TextSecondary)
        }

        if (timelineTasks.isEmpty()) {
            item {
                Column(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Box(modifier = Modifier.size(14.dp).clip(CircleShape).background(Gray))
                    Box(modifier = Modifier.width(3.dp).height(32.dp).background(Border))
                    Box(modifier = Modifier.size(14.dp).clip(CircleShape).background(Gray))
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("当天没有任务", fontSize = 16.sp, fontWeight = FontWeight.Medium, color = Gray, modifier = Modifier.semantics { contentDescription = "progress_empty" })
                }
            }
        } else {
            items(timelineTasks) { task ->
                Row(modifier = Modifier.padding(start = 14.dp)) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Box(
                            modifier = Modifier.size(14.dp).clip(CircleShape)
                                .background(if (task.status == "done") Success else Gray)
                        )
                        if (task != timelineTasks.lastOrNull()) {
                            Box(modifier = Modifier.width(3.dp).height(40.dp).background(Border))
                        }
                    }
                    Spacer(modifier = Modifier.width(20.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        val isDone = task.status == "done"
                        val timeText = if (isDone) {
                            formatCompletedAt(task.completedAt) ?: "已完成"
                        } else {
                            "未完成"
                        }
                        val submitter = if (isDone) {
                            task.completedByUsername ?: task.completedBy?.let { "用户#$it" }
                        } else {
                            null
                        }
                        val headerText = if (submitter.isNullOrBlank()) timeText else "$timeText · 提交人：$submitter"
                        Text(headerText, fontSize = 14.sp, color = TextSecondary)
                        Text(task.title, fontSize = 16.sp, fontWeight = FontWeight.Medium,
                            color = if (task.status == "done") TextPrimary else Gray)
                        if (task.photos.isNotEmpty()) {
                            AssistChip(
                                onClick = {
                                    val urls = task.photos.map { resolvePhotoUrl(it.photoUrl) }
                                    if (urls.isNotEmpty()) {
                                        photoViewerUrls = urls
                                        photoViewerIndex = 0
                                        showPhotoViewer = true
                                    }
                                },
                                label = { Text("查看照片") },
                                leadingIcon = {
                                    Icon(imageVector = Icons.Default.Photo, contentDescription = null)
                                },
                                modifier = Modifier.padding(top = 6.dp)
                            )
                        }
                    }
                }
            }
        }

        // Points summary
        item {
            Spacer(modifier = Modifier.height(8.dp))
            Surface(
                shape = RoundedCornerShape(16.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Box(
                    modifier = Modifier.background(
                        Brush.horizontalGradient(listOf(Primary, Color(0xFFFFB74D)))
                    ).padding(16.dp)
                ) {
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Column {
                            Text("今日获得", fontSize = 14.sp, color = Color.White.copy(alpha = 0.9f))
                            Text("+${p.todayPoints} 分", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Color.White, modifier = Modifier.semantics { contentDescription = "progress_points_today" })
                        }
                        Column(horizontalAlignment = Alignment.End) {
                            Text("累计积分", fontSize = 14.sp, color = Color.White.copy(alpha = 0.9f))
                            Text("${p.cumulativePoints} 分", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        }
                    }
                }
            }
        }
    }
}

private fun formatCompletedAt(value: String?): String? {
    if (value.isNullOrBlank()) return null
    val timeFormatter = DateTimeFormatter.ofPattern("HH:mm")
    return try {
        val instant = OffsetDateTime.parse(value).toInstant()
        instant.atZone(ZoneId.systemDefault()).format(timeFormatter)
    } catch (_: DateTimeParseException) {
        try {
            val instant = LocalDateTime.parse(value).atOffset(ZoneOffset.UTC).toInstant()
            instant.atZone(ZoneId.systemDefault()).format(timeFormatter)
        } catch (_: DateTimeParseException) {
            value.replace("T", " ").take(16)
        }
    }
}

private fun resolvePhotoUrl(photoUrl: String): String {
    if (photoUrl.startsWith("http://") || photoUrl.startsWith("https://")) return photoUrl
    val base = RetrofitInstance.BASE_URL.trimEnd('/')
    return if (photoUrl.startsWith("/")) base + photoUrl else "$base/$photoUrl"
}
