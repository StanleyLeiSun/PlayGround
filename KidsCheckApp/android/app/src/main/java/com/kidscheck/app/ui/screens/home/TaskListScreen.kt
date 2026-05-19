@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.kidscheck.app.ui.screens.home

import android.Manifest
import android.content.pm.PackageManager
import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.local.AppDatabase
import com.kidscheck.app.data.local.CachedDailyTask
import com.kidscheck.app.data.model.DailyTask
import com.kidscheck.app.ui.theme.*
import com.kidscheck.app.util.PhotoCompressor
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.time.LocalDate
import java.time.format.DateTimeFormatter
import kotlinx.coroutines.launch

@Composable
fun TaskListScreen(childId: Int, childName: String) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val scope = rememberCoroutineScope()
    val db = remember { AppDatabase.getInstance(context) }
    var tasks by remember { mutableStateOf<List<DailyTask>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var showCheckinSheet by remember { mutableStateOf(false) }
    var selectedTask by remember { mutableStateOf<DailyTask?>(null) }
    var showCelebration by remember { mutableStateOf(false) }
    var photoUri by remember { mutableStateOf<Uri?>(null) }
    var photoFile by remember { mutableStateOf<File?>(null) }

    val today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE)

    val cameraLauncher = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        if (success && photoFile != null) {
            scope.launch {
                try {
                    val api = RetrofitInstance.getApi(context)
                    val bytes = PhotoCompressor.compressFile(photoFile!!)
                    val part = MultipartBody.Part.createFormData(
                        "photo", photoFile!!.name,
                        bytes.toRequestBody("image/jpeg".toMediaTypeOrNull())
                    )
                    val resp = api.checkInWithPhoto(selectedTask!!.id, part)
                    if (resp.isSuccessful) {
                        showCheckinSheet = false
                        showCelebration = true
                        loadTasks(context, childId, today, db) { tasks = it; loading = false }
                        kotlinx.coroutines.delay(1500)
                        showCelebration = false
                    } else {
                        Toast.makeText(context, "打卡失败", Toast.LENGTH_SHORT).show()
                    }
                } catch (e: Exception) {
                    Toast.makeText(context, "上传失败: ${e.message}", Toast.LENGTH_SHORT).show()
                }
            }
        }
    }

    // 先展示本地缓存；真正的刷新走 onResume，确保从“模板管理”等页面返回后也会拉取最新今日任务
    LaunchedEffect(childId, today) {
        // Show cached data immediately
        val cached = db.dailyTaskDao().getTasks(childId, today)
        if (cached.isNotEmpty()) {
            tasks = cached.map { it.toDailyTask() }
            loading = false
        }
    }

    DisposableEffect(lifecycleOwner, childId, today) {
        val observer = LifecycleEventObserver { _, event ->
            if (event == Lifecycle.Event.ON_RESUME) {
                scope.launch {
                    loadTasks(context, childId, today, db) { tasks = it; loading = false }
                }
            }
        }
        lifecycleOwner.lifecycle.addObserver(observer)
        onDispose { lifecycleOwner.lifecycle.removeObserver(observer) }
    }

    Box(modifier = Modifier.fillMaxSize()) {
        if (loading) {
            CircularProgressIndicator(modifier = Modifier.align(Alignment.Center), color = Primary)
        } else if (tasks.isEmpty()) {
            Column(
                modifier = Modifier.fillMaxSize().padding(32.dp),
                horizontalAlignment = Alignment.CenterHorizontally,
                verticalArrangement = Arrangement.Center
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
                Spacer(modifier = Modifier.height(24.dp))
                Text("今天没有任务", fontSize = 18.sp, fontWeight = FontWeight.Medium, color = Gray)
                Spacer(modifier = Modifier.height(8.dp))
                Text("请家长在模板管理中添加任务", fontSize = 14.sp, color = TextSecondary)
            }
        } else {
            LazyColumn(
                modifier = Modifier.fillMaxSize().padding(16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                item {
                    Text("📋 必做任务", fontSize = 16.sp, fontWeight = FontWeight.SemiBold,
                        color = TextSecondary, modifier = Modifier.padding(bottom = 4.dp))
                }
                items(tasks.filter { !it.isConditional }) { task ->
                    TaskCard(task) {
                        selectedTask = task
                        showCheckinSheet = true
                    }
                }

                item {
                    Spacer(modifier = Modifier.height(8.dp))
                    val hasUncompleted = tasks.any { !it.isConditional && it.status == "pending" }
                    Text(
                        "🌟 条件任务${if (hasUncompleted) "（完成后解锁）" else ""}",
                        fontSize = 16.sp, fontWeight = FontWeight.SemiBold,
                        color = TextSecondary, modifier = Modifier.padding(bottom = 4.dp)
                    )
                }
                items(tasks.filter { it.isConditional }) { task ->
                    TaskCard(task) {
                        selectedTask = task
                        showCheckinSheet = true
                    }
                }
            }
        }

        // Celebration overlay
        if (showCelebration) {
            Box(
                modifier = Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.3f)),
                contentAlignment = Alignment.Center
            ) {
                Text("⭐", fontSize = 64.sp)
            }
        }

        // Check-in bottom sheet
        if (showCheckinSheet && selectedTask != null) {
            ModalBottomSheet(onDismissRequest = { showCheckinSheet = false }) {
                Column(
                    modifier = Modifier.padding(24.dp).fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text("确认完成", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(selectedTask!!.title, fontSize = 18.sp, color = TextSecondary)
                    Spacer(modifier = Modifier.height(24.dp))

                    if (selectedTask!!.type == "written") {
                        Button(
                            onClick = {
                                val file = File(context.externalCacheDir, "photo_${System.currentTimeMillis()}.jpg")
                                photoFile = file
                                val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
                                photoUri = uri
                                if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                                    cameraLauncher.launch(uri)
                                }
                            },
                            modifier = Modifier.fillMaxWidth().height(52.dp),
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Primary)
                        ) {
                            Icon(Icons.Default.CameraAlt, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("📷 拍照存证并完成", fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                        }
                    } else {
                        Button(
                            onClick = {
                                scope.launch {
                                    try {
                                        val resp = RetrofitInstance.getApi(context).checkIn(selectedTask!!.id)
                                        if (resp.isSuccessful) {
                                            showCheckinSheet = false
                                            showCelebration = true
                                            loadTasks(context, childId, today, db) { tasks = it; loading = false }
                                            kotlinx.coroutines.delay(1500)
                                            showCelebration = false
                                        }
                                    } catch (e: Exception) {
                                        Toast.makeText(context, "打卡失败", Toast.LENGTH_SHORT).show()
                                    }
                                }
                            },
                            modifier = Modifier.fillMaxWidth().height(52.dp),
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Success)
                        ) {
                            Text("✓ 确认完成", fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                        }
                    }

                    Spacer(modifier = Modifier.height(12.dp))
                    TextButton(onClick = { showCheckinSheet = false }) {
                        Text("取消", color = Gray, fontSize = 16.sp)
                    }
                }
            }
        }
    }
}

@Composable
fun TaskCard(task: DailyTask, onClick: () -> Unit) {
    val isDone = task.status == "done"
    val bgColor = when {
        isDone -> SuccessLight
        else -> MaterialTheme.colorScheme.surface
    }
    val borderColor = when {
        isDone -> Success
        else -> Border
    }

    Surface(
        modifier = Modifier.fillMaxWidth().clickable(enabled = !isDone, onClick = onClick),
        shape = RoundedCornerShape(16.dp),
        color = bgColor,
        border = androidx.compose.foundation.BorderStroke(2.dp, borderColor)
    ) {
        Row(
            modifier = Modifier.padding(16.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Box(
                modifier = Modifier.size(28.dp).clip(CircleShape)
                    .background(if (isDone) Success else Color.Transparent)
                    .then(if (!isDone) Modifier.background(Color.Transparent) else Modifier),
                contentAlignment = Alignment.Center
            ) {
                if (isDone) {
                    Icon(Icons.Default.Check, contentDescription = null, tint = Color.White, modifier = Modifier.size(16.dp))
                } else {
                    Surface(modifier = Modifier.size(28.dp), shape = CircleShape, color = Color.Transparent,
                        border = androidx.compose.foundation.BorderStroke(3.dp, Gray)) {}
                }
            }

            Spacer(modifier = Modifier.width(14.dp))

            Column(modifier = Modifier.weight(1f)) {
                Text(task.title, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                if (task.type == "written") {
                    Surface(shape = RoundedCornerShape(10.dp), color = PrimaryLight) {
                        Text("📷 拍照", modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                            fontSize = 12.sp, color = Primary)
                    }
                }
            }

            Text("+${task.points}分", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Primary)
        }
    }
}

private suspend fun loadTasks(
    context: android.content.Context,
    childId: Int,
    date: String,
    db: AppDatabase,
    onResult: (List<DailyTask>) -> Unit
) {
    try {
        val resp = RetrofitInstance.getApi(context).getDailyTasks(childId, date)
        if (resp.isSuccessful) {
            val taskList = resp.body() ?: emptyList()
            onResult(taskList)
            db.dailyTaskDao().clearFor(childId, date)
            db.dailyTaskDao().insertAll(taskList.map { it.toCached(childId, date) })
        } else {
            onResult(emptyList())
        }
    } catch (_: Exception) {
        onResult(emptyList())
    }
}

private fun CachedDailyTask.toDailyTask() = DailyTask(
    id = id,
    childId = childId,
    date = date,
    title = title,
    type = type,
    points = points,
    status = status,
    completedAt = completedAt,
    completedBy = completedBy,
    isConditional = isConditional,
    photos = emptyList()
)

private fun DailyTask.toCached(childId: Int, date: String) = CachedDailyTask(
    id = id,
    childId = childId,
    date = date,
    title = title,
    type = type,
    points = points,
    status = status,
    completedAt = completedAt,
    completedBy = completedBy,
    isConditional = isConditional
)
