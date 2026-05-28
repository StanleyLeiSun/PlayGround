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
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
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
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun TaskListScreen(childId: Int, childName: String) {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    val scope = rememberCoroutineScope()
    val db = remember { AppDatabase.getInstance(context) }
    var tasks by remember { mutableStateOf<List<DailyTask>>(emptyList()) }
    var loading by remember { mutableStateOf(true) }
    var showCheckinSheet by remember { mutableStateOf(false) }
    var showUndoDialog by remember { mutableStateOf(false) }
    var selectedTask by remember { mutableStateOf<DailyTask?>(null) }
    var showCelebration by remember { mutableStateOf(false) }
    var showAdhocDialog by remember { mutableStateOf(false) }
    var photoUri by remember { mutableStateOf<Uri?>(null) }
    var photoFile by remember { mutableStateOf<File?>(null) }

    val today = LocalDate.now().format(DateTimeFormatter.ISO_LOCAL_DATE)

    fun uploadPhotoAndCheckIn(bytes: ByteArray, fileName: String) {
        scope.launch {
            try {
                val api = RetrofitInstance.getApi(context)
                val part = MultipartBody.Part.createFormData(
                    "photo", fileName,
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
                    withContext(Dispatchers.Main) { Toast.makeText(context, "打卡失败", Toast.LENGTH_SHORT).show() }
                }
            } catch (e: Exception) {
                withContext(Dispatchers.Main) { Toast.makeText(context, "上传失败: ${e.message}", Toast.LENGTH_SHORT).show() }
            }
        }
    }

    val cameraLauncher = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        if (success && photoFile != null) {
            val bytes = PhotoCompressor.compressFile(photoFile!!)
            uploadPhotoAndCheckIn(bytes, photoFile!!.name)
        }
    }

    val galleryLauncher = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) {
            val bytes = PhotoCompressor.compressPhoto(context, uri)
            uploadPhotoAndCheckIn(bytes, "gallery_${System.currentTimeMillis()}.jpg")
        }
    }

    val cameraPermissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) {
            photoUri?.let { cameraLauncher.launch(it) }
        } else {
            Toast.makeText(context, "需要相机权限才能拍照", Toast.LENGTH_SHORT).show()
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
            CircularProgressIndicator(modifier = Modifier.align(Alignment.Center).semantics { contentDescription = "task_list_loading" }, color = Primary)
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
                Text("今天没有任务", fontSize = 18.sp, fontWeight = FontWeight.Medium, color = Gray, modifier = Modifier.semantics { contentDescription = "task_list_empty" })
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
                        if (task.status == "done") showUndoDialog = true
                        else showCheckinSheet = true
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
                        if (task.status == "done") showUndoDialog = true
                        else showCheckinSheet = true
                    }
                }
            }
        }

        // FAB for adhoc task
        FloatingActionButton(
            onClick = { showAdhocDialog = true },
            modifier = Modifier.align(Alignment.BottomEnd).padding(16.dp).semantics { contentDescription = "task_adhoc_fab" },
            containerColor = Primary
        ) {
            Icon(Icons.Default.Add, contentDescription = "添加临时任务", tint = Color.White)
        }

        // Celebration overlay
        if (showCelebration) {
            Box(
                modifier = Modifier.fillMaxSize().background(Color.Black.copy(alpha = 0.3f)).semantics { contentDescription = "task_celebration" },
                contentAlignment = Alignment.Center
            ) {
                Text("⭐", fontSize = 64.sp)
            }
        }

        // Adhoc task dialog
        if (showAdhocDialog) {
            AddAdhocTaskDialog(
                onDismiss = { showAdhocDialog = false },
                onConfirm = { data ->
                    scope.launch {
                        try {
                            val api = RetrofitInstance.getApi(context)
                            val resp = api.createAdhocTask(childId, data)
                            if (resp.isSuccessful) {
                                showAdhocDialog = false
                                loadTasks(context, childId, today, db) { tasks = it; loading = false }
                            } else {
                                withContext(Dispatchers.Main) { Toast.makeText(context, "添加失败", Toast.LENGTH_SHORT).show() }
                            }
                        } catch (e: Exception) {
                            withContext(Dispatchers.Main) { Toast.makeText(context, "添加失败: ${e.message}", Toast.LENGTH_SHORT).show() }
                        }
                    }
                }
            )
        }

        // Undo dialog
        if (showUndoDialog && selectedTask != null) {
            AlertDialog(
                onDismissRequest = { showUndoDialog = false },
                title = { Text("撤销完成") },
                text = { Text("确定要撤销「${selectedTask!!.title}」的完成状态吗？积分将被扣回。") },
                confirmButton = {
                    TextButton(onClick = {
                        scope.launch {
                            try {
                                val resp = RetrofitInstance.getApi(context).undoCheckIn(selectedTask!!.id)
                                if (resp.isSuccessful) {
                                    showUndoDialog = false
                                    loadTasks(context, childId, today, db) { tasks = it; loading = false }
                                    withContext(Dispatchers.Main) { Toast.makeText(context, "已撤销", Toast.LENGTH_SHORT).show() }
                                } else {
                                    withContext(Dispatchers.Main) { Toast.makeText(context, "撤销失败", Toast.LENGTH_SHORT).show() }
                                }
                            } catch (e: Exception) {
                                withContext(Dispatchers.Main) { Toast.makeText(context, "撤销失败: ${e.message}", Toast.LENGTH_SHORT).show() }
                            }
                        }
                    }) { Text("确认撤销", color = Warning, modifier = Modifier.semantics { contentDescription = "task_undo_confirm" }) }
                },
                dismissButton = { TextButton(onClick = { showUndoDialog = false }) { Text("取消") } }
            )
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
                                } else {
                                    cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                                }
                            },
                            modifier = Modifier.fillMaxWidth().height(52.dp),
                            shape = RoundedCornerShape(14.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Primary)
                        ) {
                            Icon(Icons.Default.CameraAlt, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("拍照存证并完成", fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                        }
                        Spacer(modifier = Modifier.height(10.dp))
                        OutlinedButton(
                            onClick = { galleryLauncher.launch("image/*") },
                            modifier = Modifier.fillMaxWidth().height(52.dp),
                            shape = RoundedCornerShape(14.dp)
                        ) {
                            Icon(Icons.Default.PhotoLibrary, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("从相册选择并完成", fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
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
                                        withContext(Dispatchers.Main) { Toast.makeText(context, "打卡失败", Toast.LENGTH_SHORT).show() }
                                    }
                                }
                            },
                            modifier = Modifier.fillMaxWidth().height(52.dp).semantics { contentDescription = "task_checkin_confirm" },
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
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick).semantics { contentDescription = "task_card_${task.id}" },
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
                if (!task.description.isNullOrBlank()) {
                    Text(task.description, fontSize = 13.sp, color = Gray, maxLines = 2)
                }
                Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    if (task.type == "written") {
                        Surface(shape = RoundedCornerShape(10.dp), color = PrimaryLight) {
                            Text("📷 拍照", modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                                fontSize = 12.sp, color = Primary)
                        }
                    }
                    if (task.isAdhoc) {
                        Surface(shape = RoundedCornerShape(10.dp), color = WarningLight) {
                            Text("临时", modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                                fontSize = 12.sp, color = Warning)
                        }
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
        }
    } catch (_: Exception) {}
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

@Composable
fun AddAdhocTaskDialog(onDismiss: () -> Unit, onConfirm: (com.kidscheck.app.data.model.AdhocTaskCreate) -> Unit) {
    var title by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var requirePhoto by remember { mutableStateOf(false) }
    var points by remember { mutableStateOf("5") }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("添加临时任务") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = title, onValueChange = { title = it }, label = { Text("任务名称") }, singleLine = true, modifier = Modifier.semantics { contentDescription = "task_adhoc_title" })
                OutlinedTextField(value = description, onValueChange = { description = it }, label = { Text("备注（可选）") }, singleLine = true)
                OutlinedTextField(value = points, onValueChange = { points = it }, label = { Text("积分") }, singleLine = true)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = requirePhoto, onCheckedChange = { requirePhoto = it })
                    Text("要求拍照", fontSize = 14.sp)
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    if (title.isNotBlank()) {
                        val type = if (requirePhoto) "written" else "reading"
                        onConfirm(com.kidscheck.app.data.model.AdhocTaskCreate(title, type, description.ifBlank { null }, points.toIntOrNull() ?: 5))
                    }
                },
                enabled = title.isNotBlank()
            ) { Text("添加") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("取消") } }
    )
}
