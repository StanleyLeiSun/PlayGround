package com.kidscheck.app.ui.screens.progress

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
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
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.DailyTask
import com.kidscheck.app.data.model.ProgressResponse
import com.kidscheck.app.ui.theme.*
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import kotlinx.coroutines.launch

@Composable
fun ProgressScreen(childId: Int) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var progress by remember { mutableStateOf<ProgressResponse?>(null) }
    var currentDate by remember { mutableStateOf(LocalDate.now()) }
    var loading by remember { mutableStateOf(true) }

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
            CircularProgressIndicator(color = Primary)
        }
        return
    }

    val p = progress ?: return

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
                IconButton(onClick = { currentDate = currentDate.minusDays(1) }) {
                    Icon(Icons.Default.ChevronLeft, "上一天")
                }
                Text(
                    "${currentDate.monthValue}月${currentDate.dayOfMonth}日",
                    fontSize = 16.sp, fontWeight = FontWeight.SemiBold
                )
                IconButton(onClick = { currentDate = currentDate.plusDays(1) }) {
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

        if (p.tasks.isEmpty()) {
            item {
                Column(
                    modifier = Modifier.fillMaxWidth().padding(vertical = 24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Box(
                        modifier = Modifier.size(14.dp).clip(CircleShape).background(Gray)
                    )
                    Box(modifier = Modifier.width(3.dp).height(32.dp).background(Border))
                    Box(
                        modifier = Modifier.size(14.dp).clip(CircleShape).background(Gray)
                    )
                    Box(modifier = Modifier.width(3.dp).height(32.dp).background(Border))
                    Box(
                        modifier = Modifier.size(14.dp).clip(CircleShape).background(Gray)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("当天没有任务", fontSize = 16.sp, fontWeight = FontWeight.Medium, color = Gray)
                }
            }
        } else {
            items(p.tasks.sortedWith(compareBy<DailyTask> { it.isConditional }.thenBy { it.completedAt ?: "zzz" })) { task ->
                Row(modifier = Modifier.padding(start = 14.dp)) {
                    // Timeline line + dot
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Box(
                            modifier = Modifier.size(14.dp).clip(CircleShape)
                                .background(if (task.status == "done") Success else Gray)
                        )
                        if (task != p.tasks.last()) {
                            Box(modifier = Modifier.width(3.dp).height(40.dp).background(Border))
                        }
                    }
                    Spacer(modifier = Modifier.width(20.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text(
                            task.completedAt?.take(16)?.replace("T", " ") ?: "--:--",
                            fontSize = 14.sp, color = Gray
                        )
                        Text(task.title, fontSize = 16.sp, fontWeight = FontWeight.Medium,
                            color = if (task.status == "done") TextPrimary else Gray)
                        if (task.photos.isNotEmpty()) {
                            Text("📷 查看照片", fontSize = 13.sp, color = Primary,
                                modifier = Modifier.clickable { /* open photo */ })
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
                            Text("+${p.todayPoints} 分", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Color.White)
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
