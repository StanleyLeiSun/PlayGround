@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.kidscheck.app.ui.screens.insights

import android.widget.Toast
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.InsightsResponse
import com.kidscheck.app.data.model.TaskStatItem
import com.kidscheck.app.ui.theme.*
import kotlinx.coroutines.launch

@Composable
fun DataInsightsScreen(childId: Int) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var period by remember { mutableStateOf("week") }
    var data by remember { mutableStateOf<InsightsResponse?>(null) }
    var loading by remember { mutableStateOf(true) }

    fun load() {
        scope.launch {
            loading = true
            try {
                val resp = RetrofitInstance.getApi(context).getInsights(childId, period)
                if (resp.isSuccessful) {
                    data = resp.body()
                } else {
                    Toast.makeText(context, "加载失败", Toast.LENGTH_SHORT).show()
                }
            } catch (_: Exception) {
                Toast.makeText(context, "网络错误", Toast.LENGTH_SHORT).show()
            }
            loading = false
        }
    }

    LaunchedEffect(childId, period) { load() }

    if (loading && data == null) {
        Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
            CircularProgressIndicator(color = Primary)
        }
        return
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Period selector
        item {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilterChip(
                    selected = period == "week",
                    onClick = { period = "week" },
                    label = { Text("本周") },
                    modifier = Modifier.semantics { contentDescription = "insights_period_week" }
                )
                FilterChip(
                    selected = period == "last_week",
                    onClick = { period = "last_week" },
                    label = { Text("上一周") },
                    modifier = Modifier.semantics { contentDescription = "insights_period_last_week" }
                )
                FilterChip(
                    selected = period == "month",
                    onClick = { period = "month" },
                    label = { Text("本月") },
                    modifier = Modifier.semantics { contentDescription = "insights_period_month" }
                )
            }
        }

        data?.let { insights ->
            // Summary cards
            item {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    SummaryCard(
                        modifier = Modifier.weight(1f),
                        label = "完成率",
                        value = "${insights.completionRate}%",
                        sub = "${insights.completedTasks}/${insights.totalTasks}"
                    )
                    SummaryCard(
                        modifier = Modifier.weight(1f),
                        label = "总积分",
                        value = "${insights.totalPointsEarned}",
                        sub = "本期获得"
                    )
                    SummaryCard(
                        modifier = Modifier.weight(1f),
                        label = "连续打卡",
                        value = "${insights.streak}天",
                        sub = "全部完成"
                    )
                }
            }

            // Completion rate ring
            item {
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = MaterialTheme.colorScheme.surface,
                    tonalElevation = 1.dp
                ) {
                    Column(
                        modifier = Modifier.fillMaxWidth().padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        Text("完成率", fontSize = 14.sp, color = TextSecondary)
                        Spacer(Modifier.height(8.dp))
                        CompletionRing(rate = insights.completionRate / 100f)
                    }
                }
            }

            // Daily bar chart
            item {
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = MaterialTheme.colorScheme.surface,
                    tonalElevation = 1.dp
                ) {
                    Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
                        Text("每日完成情况", fontSize = 14.sp, color = TextSecondary)
                        Spacer(Modifier.height(12.dp))
                        DailyBarChart(insights.dailyStats.map {
                            if (it.total > 0) it.completed.toFloat() / it.total else 0f
                        })
                        Spacer(Modifier.height(4.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            val stats = insights.dailyStats
                            if (stats.isNotEmpty()) {
                                Text(stats.first().date.takeLast(5), fontSize = 11.sp, color = Gray)
                                Text(stats.last().date.takeLast(5), fontSize = 11.sp, color = Gray)
                            }
                        }
                    }
                }
            }

            // Task completion stats
            item {
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    color = MaterialTheme.colorScheme.surface,
                    tonalElevation = 1.dp
                ) {
                    Column(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
                        Text("任务完成明细", fontSize = 14.sp, color = TextSecondary)
                        Spacer(Modifier.height(12.dp))
                        if (insights.taskStats.isNotEmpty()) {
                            Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                                insights.taskStats.forEach { stat ->
                                    TaskStatRow(stat)
                                }
                            }
                        } else {
                            Text("暂无数据", color = Gray, fontSize = 14.sp)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SummaryCard(modifier: Modifier, label: String, value: String, sub: String) {
    Surface(
        modifier = modifier,
        shape = RoundedCornerShape(14.dp),
        color = PrimaryLight
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(label, fontSize = 12.sp, color = TextSecondary)
            Spacer(Modifier.height(4.dp))
            Text(value, fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Primary)
            Text(sub, fontSize = 11.sp, color = Gray)
        }
    }
}

@Composable
private fun CompletionRing(rate: Float) {
    val primaryColor = Primary
    val bgColor = Border
    Box(contentAlignment = Alignment.Center, modifier = Modifier.size(120.dp)) {
        Canvas(modifier = Modifier.size(100.dp)) {
            val stroke = Stroke(width = 12.dp.toPx(), cap = StrokeCap.Round)
            drawArc(color = bgColor, startAngle = -90f, sweepAngle = 360f, useCenter = false, style = stroke)
            drawArc(color = primaryColor, startAngle = -90f, sweepAngle = 360f * rate, useCenter = false, style = stroke)
        }
        Text("${(rate * 100).toInt()}%", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Primary)
    }
}

@Composable
private fun DailyBarChart(rates: List<Float>) {
    val primaryColor = Primary
    val bgColor = Border
    Canvas(modifier = Modifier.fillMaxWidth().height(80.dp)) {
        if (rates.isEmpty()) return@Canvas
        val barWidth = size.width / rates.size * 0.6f
        val gap = size.width / rates.size * 0.4f
        rates.forEachIndexed { i, rate ->
            val x = i * (barWidth + gap) + gap / 2
            // Background bar
            drawRect(
                color = bgColor,
                topLeft = Offset(x, 0f),
                size = Size(barWidth, size.height)
            )
            // Filled bar
            val filledHeight = size.height * rate
            drawRect(
                color = primaryColor,
                topLeft = Offset(x, size.height - filledHeight),
                size = Size(barWidth, filledHeight)
            )
        }
    }
}

@Composable
private fun TaskStatRow(stat: TaskStatItem) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            stat.title,
            fontSize = 14.sp,
            fontWeight = FontWeight.Medium,
            color = TextPrimary,
            modifier = Modifier.weight(1f)
        )
        Text(
            "${stat.completed}/${stat.total}天",
            fontSize = 13.sp,
            color = TextSecondary,
            modifier = Modifier.padding(end = 12.dp)
        )
        LinearProgressIndicator(
            progress = stat.ratio,
            modifier = Modifier.width(80.dp).height(8.dp).clip(RoundedCornerShape(4.dp)),
            color = if (stat.ratio >= 0.8f) Success else Primary,
            trackColor = Border
        )
    }
}
