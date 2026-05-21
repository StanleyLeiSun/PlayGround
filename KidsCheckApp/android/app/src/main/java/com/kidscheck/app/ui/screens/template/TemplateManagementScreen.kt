@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class, androidx.compose.foundation.layout.ExperimentalLayoutApi::class)

package com.kidscheck.app.ui.screens.template

import android.app.Activity
import android.content.Intent
import android.speech.RecognizerIntent
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.*
import com.kidscheck.app.ui.theme.*
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import java.util.Locale

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TemplateManagementScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var children by remember { mutableStateOf<List<Child>>(emptyList()) }
    var selectedChild by remember { mutableStateOf<Child?>(null) }
    var templates by remember { mutableStateOf<List<TemplatesByWeekday>>(emptyList()) }
    var conditionals by remember { mutableStateOf<List<ConditionalTask>>(emptyList()) }
    var showAddDialog by remember { mutableStateOf(false) }
    var voiceResult by remember { mutableStateOf<VoiceParsedIntent?>(null) }
    var showVoiceConfirm by remember { mutableStateOf(false) }
    var reloadJob by remember { mutableStateOf<Job?>(null) }

    val speechLauncher = rememberLauncherForActivityResult(ActivityResultContracts.StartActivityForResult()) { result ->
        if (result.resultCode == Activity.RESULT_OK) {
            val matches = result.data?.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS)
            val text = matches?.firstOrNull()
            if (text != null) {
                scope.launch {
                    try {
                        val resp = RetrofitInstance.getApi(context).voiceInput(VoiceRequest(text))
                        if (resp.isSuccessful) {
                            voiceResult = resp.body()
                            showVoiceConfirm = true
                        }
                    } catch (e: Exception) {
                        Toast.makeText(context, "语音解析失败", Toast.LENGTH_SHORT).show()
                    }
                }
            }
        }
    }

    fun reload() {
        reloadJob?.cancel()
        reloadJob = scope.launch {
            try {
                val api = RetrofitInstance.getApi(context)
                selectedChild?.let { child ->
                    val tResp = api.getTemplates(child.id)
                    if (tResp.isSuccessful) templates = tResp.body() ?: emptyList()
                    val cResp = api.getConditionalTasks(child.id)
                    if (cResp.isSuccessful) conditionals = cResp.body() ?: emptyList()
                }
            } catch (_: Exception) {}
        }
    }

    LaunchedEffect(Unit) {
        scope.launch {
            try {
                val resp = RetrofitInstance.getApi(context).getChildren()
                if (resp.isSuccessful) {
                    children = resp.body() ?: emptyList()
                    selectedChild = children.firstOrNull()
                    reload()
                }
            } catch (_: Exception) {}
        }
    }

    LaunchedEffect(selectedChild) { reload() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("任务模板管理", fontWeight = FontWeight.Bold) },
                navigationIcon = {
                    IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "返回") }
                },
                actions = {
                    IconButton(onClick = {
                        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                            putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.CHINESE)
                        }
                        speechLauncher.launch(intent)
                    }) {
                        Icon(Icons.Default.Mic, "语音输入", tint = Primary)
                    }
                }
            )
        },
        floatingActionButton = {
            FloatingActionButton(onClick = { showAddDialog = true }, containerColor = Primary) {
                Icon(Icons.Default.Add, "添加", tint = androidx.compose.ui.graphics.Color.White)
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier.padding(padding).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            // Child tabs
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    children.forEach { child ->
                        FilterChip(
                            selected = selectedChild?.id == child.id,
                            onClick = { selectedChild = child },
                            label = { Text(child.nickname) }
                        )
                    }
                }
                Spacer(modifier = Modifier.height(8.dp))
            }

            // Templates by weekday
            templates.forEach { group ->
                item {
                    Text(group.weekdayName, fontSize = 16.sp, fontWeight = FontWeight.Bold,
                        color = Primary, modifier = Modifier.padding(vertical = 4.dp))
                }
                items(group.templates) { template ->
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text(template.title, fontSize = 16.sp, modifier = Modifier.weight(1f))
                        if (template.type == "written") {
                            Surface(shape = RoundedCornerShape(8.dp), color = PrimaryLight) {
                                Text("📷 拍照", modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                                    fontSize = 12.sp, color = Primary)
                            }
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("${template.points}分", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Primary)
                        IconButton(onClick = {
                            scope.launch {
                                RetrofitInstance.getApi(context).deleteTemplate(template.id)
                                reload()
                            }
                        }) {
                            Icon(Icons.Default.Delete, "删除", tint = Danger, modifier = Modifier.size(20.dp))
                        }
                    }
                }
            }

            // Conditional tasks
            if (conditionals.isNotEmpty()) {
                item {
                    Spacer(modifier = Modifier.height(12.dp))
                    Text("🌟 条件任务", fontSize = 16.sp, fontWeight = FontWeight.Bold,
                        color = Purple, modifier = Modifier.padding(vertical = 4.dp))
                }
                items(conditionals) { task ->
                    Row(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                        Text(task.title, fontSize = 16.sp, modifier = Modifier.weight(1f))
                        Surface(shape = RoundedCornerShape(8.dp), color = PurpleLight) {
                            Text("条件", modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                                fontSize = 12.sp, color = Purple)
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("${task.points}分", fontSize = 14.sp, fontWeight = FontWeight.SemiBold, color = Primary)
                        IconButton(onClick = {
                            scope.launch {
                                RetrofitInstance.getApi(context).deleteConditionalTask(task.id)
                                reload()
                            }
                        }) {
                            Icon(Icons.Default.Delete, "删除", tint = Danger, modifier = Modifier.size(20.dp))
                        }
                    }
                }
            }
        }
    }

    // Add template dialog
    if (showAddDialog) {
        AddTemplateDialog(
            onDismiss = { showAddDialog = false },
            onConfirm = { data, isConditional ->
                scope.launch {
                    try {
                        val api = RetrofitInstance.getApi(context)
                        val resp = if (isConditional && selectedChild != null) {
                            api.createConditionalTask(selectedChild!!.id, ConditionalTaskCreate(data.title, data.type, data.description, data.points))
                        } else if (selectedChild != null) {
                            api.createTemplateBatch(selectedChild!!.id, data)
                        } else null
                        if (resp != null && resp.isSuccessful) {
                            showAddDialog = false
                            reload()
                        } else {
                            val code = resp?.code() ?: -1
                            val errBody = resp?.errorBody()?.string() ?: ""
                            Toast.makeText(context, "添加失败 (HTTP $code): $errBody", Toast.LENGTH_LONG).show()
                        }
                    } catch (e: Exception) {
                        Toast.makeText(context, "添加失败: ${e.message}", Toast.LENGTH_LONG).show()
                    }
                }
            }
        )
    }

    // Voice confirm dialog
    if (showVoiceConfirm && voiceResult != null) {
        val intent = voiceResult!!
        AlertDialog(
            onDismissRequest = { showVoiceConfirm = false },
            title = { Text("确认操作") },
            text = {
                Column {
                    Text("动作: ${intent.action}")
                    intent.child?.let { Text("孩子: $it") }
                    intent.weekday?.let { Text("星期: $it") }
                    intent.title?.let { Text("任务: $it") }
                    intent.points?.let { Text("积分: $it") }
                    Text("要求拍照: ${if (intent.type == "written") "是" else "否"}")
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    scope.launch {
                        try {
                            val api = RetrofitInstance.getApi(context)
                            val child = children.find { it.nickname == intent.child } ?: selectedChild
                            if (child != null && intent.action == "create" && intent.title != null && intent.weekday != null) {
                                if (intent.isConditional) {
                                    api.createConditionalTask(child.id, ConditionalTaskCreate(intent.title, intent.type ?: "written", points = intent.points ?: 5))
                                } else {
                                    api.createTemplate(child.id, TaskTemplateCreate(intent.weekday, intent.title, intent.type ?: "written", points = intent.points ?: 5))
                                }
                            }
                            showVoiceConfirm = false
                            reload()
                        } catch (_: Exception) {}
                    }
                }) { Text("确认") }
            },
            dismissButton = { TextButton(onClick = { showVoiceConfirm = false }) { Text("取消") } }
        )
    }
}

@Composable
fun AddTemplateDialog(onDismiss: () -> Unit, onConfirm: (TaskTemplateBatchCreate, Boolean) -> Unit) {
    var title by remember { mutableStateOf("") }
    var description by remember { mutableStateOf("") }
    var selectedDays by remember { mutableStateOf(setOf(1)) }
    var requirePhoto by remember { mutableStateOf(false) }
    var points by remember { mutableStateOf("5") }
    var isConditional by remember { mutableStateOf(false) }

    AlertDialog(
        onDismissRequest = onDismiss,
        title = { Text("添加任务") },
        text = {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(value = title, onValueChange = { title = it }, label = { Text("任务名称") }, singleLine = true)
                OutlinedTextField(value = description, onValueChange = { description = it }, label = { Text("备注（可选）") }, singleLine = true)
                if (!isConditional) {
                    Text("周几（可多选）:", fontSize = 14.sp)
                    FlowRow(horizontalArrangement = Arrangement.spacedBy(4.dp), verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        (1..7).forEach { d ->
                            FilterChip(
                                selected = d in selectedDays,
                                onClick = {
                                    selectedDays = if (d in selectedDays) selectedDays - d else selectedDays + d
                                },
                                label = { Text(listOf("一","二","三","四","五","六","日")[d-1], fontSize = 12.sp) }
                            )
                        }
                    }
                }
                OutlinedTextField(value = points, onValueChange = { points = it }, label = { Text("积分") }, singleLine = true)
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = requirePhoto, onCheckedChange = { requirePhoto = it })
                    Text("要求拍照", fontSize = 14.sp)
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Checkbox(checked = isConditional, onCheckedChange = { isConditional = it })
                    Text("条件任务", fontSize = 14.sp)
                }
            }
        },
        confirmButton = {
            TextButton(
                onClick = {
                    if (title.isNotBlank() && (isConditional || selectedDays.isNotEmpty())) {
                        val type = if (requirePhoto) "written" else "reading"
                        onConfirm(TaskTemplateBatchCreate(selectedDays.sorted(), title, type, description = description.ifBlank { null }, points = points.toIntOrNull() ?: 5), isConditional)
                    }
                },
                enabled = title.isNotBlank() && (isConditional || selectedDays.isNotEmpty())
            ) { Text("添加") }
        },
        dismissButton = { TextButton(onClick = onDismiss) { Text("取消") } }
    )
}
