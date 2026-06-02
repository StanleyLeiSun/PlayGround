package com.kidscheck.app.ui.screens.home

import android.Manifest
import android.content.Context
import android.media.MediaPlayer
import android.media.MediaRecorder
import android.os.Build
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.DailyTask
import com.kidscheck.app.data.model.OralRecordingSubmitResponse
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import java.util.Locale

private enum class OralState { READY, RECORDING, RECORDED, SUBMITTING, DONE }

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun OralPracticeScreen(
    task: DailyTask,
    baseUrl: String,
    onBack: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val snackbarHostState = remember { SnackbarHostState() }

    var state by remember { mutableStateOf(OralState.READY) }
    var elapsedTime by remember { mutableLongStateOf(0L) }
    var recordedDuration by remember { mutableFloatStateOf(0f) }
    var tempAudioFile by remember { mutableStateOf<File?>(null) }
    var mediaPlayer by remember { mutableStateOf<MediaPlayer?>(null) }
    var isPlaying by remember { mutableStateOf(false) }
    var playbackPosition by remember { mutableFloatStateOf(0f) }
    var scale by remember { mutableFloatStateOf(1f) }
    var offsetX by remember { mutableFloatStateOf(0f) }
    var offsetY by remember { mutableFloatStateOf(0f) }

    // MediaRecorder reference
    var mediaRecorder by remember { mutableStateOf<MediaRecorder?>(null) }

    // Permission launcher
    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            // Start recording after permission granted
            scope.launch {
                val file = File(context.cacheDir, "oral_${System.currentTimeMillis()}.m4a")
                tempAudioFile = file
                mediaRecorder = startRecording(context, file)
                state = OralState.RECORDING
                elapsedTime = 0L
            }
        }
    }

    // Timer for recording
    LaunchedEffect(state) {
        if (state == OralState.RECORDING) {
            while (state == OralState.RECORDING) {
                delay(1000)
                elapsedTime++
                // Auto-stop at 5 minutes
                if (elapsedTime >= 300) {
                    mediaRecorder?.stop()
                    mediaRecorder?.release()
                    mediaRecorder = null
                    recordedDuration = elapsedTime.toFloat()
                    state = OralState.RECORDED
                }
            }
        }
    }

    // Cleanup on dispose
    DisposableEffect(Unit) {
        onDispose {
            mediaRecorder?.release()
            mediaPlayer?.release()
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        topBar = {
            TopAppBar(
                title = { Text("英语口语练习") },
                navigationIcon = {
                    IconButton(
                        onClick = onBack,
                        enabled = state != OralState.RECORDING
                    ) {
                        Icon(Icons.AutoMirrored.Filled.ArrowBack, "返回")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Task title
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.primaryContainer
                )
            ) {
                Text(
                    text = task.title,
                    modifier = Modifier.padding(12.dp),
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.onPrimaryContainer
                )
                if (task.description != null) {
                    Text(
                        text = task.description,
                        modifier = Modifier.padding(horizontal = 12.dp, vertical = 4.dp),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onPrimaryContainer.copy(alpha = 0.7f)
                    )
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Image area - takes most of the space
            val imageUrl = task.oralImageUrl?.let { "$baseUrl$it" }
            if (imageUrl != null) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f)
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color(0xFFE2E8F0))
                        .pointerInput(Unit) {
                            detectTransformGestures { _, pan, zoom, _ ->
                                scale = (scale * zoom).coerceIn(0.5f, 5f)
                                offsetX += pan.x
                                offsetY += pan.y
                            }
                        },
                    contentAlignment = Alignment.Center
                ) {
                    AsyncImage(
                        model = imageUrl,
                        contentDescription = "练习图片",
                        modifier = Modifier
                            .fillMaxSize()
                            .graphicsLayer(
                                scaleX = scale,
                                scaleY = scale,
                                translationX = offsetX,
                                translationY = offsetY
                            ),
                        contentScale = ContentScale.Fit
                    )
                    // Hint badge
                    Box(
                        modifier = Modifier
                            .align(Alignment.BottomEnd)
                            .padding(8.dp)
                            .background(Color.Black.copy(alpha = 0.5f), RoundedCornerShape(4.dp))
                            .padding(horizontal = 8.dp, vertical = 4.dp)
                    ) {
                        Text("↕ 滑动 · 🔍 缩放", color = Color.White, fontSize = 11.sp)
                    }
                }
            } else {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .weight(1f)
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color(0xFFE2E8F0)),
                    contentAlignment = Alignment.Center
                ) {
                    Text("暂无练习图片", color = Color.Gray)
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Bottom controls based on state
            when (state) {
                OralState.READY -> ReadyControls(
                    onStartRecording = {
                        permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                    }
                )
                OralState.RECORDING -> RecordingControls(
                    elapsedTime = elapsedTime,
                    canStop = elapsedTime >= 20,
                    onStop = {
                        mediaRecorder?.stop()
                        mediaRecorder?.release()
                        mediaRecorder = null
                        recordedDuration = elapsedTime.toFloat()
                        state = OralState.RECORDED
                    }
                )
                OralState.RECORDED -> RecordedControls(
                    duration = recordedDuration,
                    context = context,
                    audioFile = tempAudioFile,
                    mediaPlayer = mediaPlayer,
                    isPlaying = isPlaying,
                    playbackPosition = playbackPosition,
                    onPlayPause = {
                        if (isPlaying) {
                            mediaPlayer?.pause()
                            isPlaying = false
                        } else {
                            if (mediaPlayer == null && tempAudioFile != null) {
                                mediaPlayer = MediaPlayer().apply {
                                    setDataSource(tempAudioFile!!.absolutePath)
                                    prepare()
                                    setOnCompletionListener {
                                        isPlaying = false
                                        playbackPosition = 0f
                                    }
                                }
                            }
                            mediaPlayer?.start()
                            isPlaying = true
                        }
                    },
                    onReRecord = {
                        mediaPlayer?.release()
                        mediaPlayer = null
                        isPlaying = false
                        playbackPosition = 0f
                        state = OralState.READY
                    },
                    onSubmit = {
                        state = OralState.SUBMITTING
                        scope.launch {
                            val error = submitRecording(context, task.id, tempAudioFile!!, recordedDuration)
                            if (error == null) {
                                state = OralState.DONE
                                delay(1500)
                                onBack()
                            } else {
                                snackbarHostState.showSnackbar(error)
                                state = OralState.RECORDED
                            }
                        }
                    }
                )
                OralState.SUBMITTING -> {
                    CircularProgressIndicator()
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("提交中...")
                }
                OralState.DONE -> {
                    Icon(
                        Icons.Default.CheckCircle,
                        contentDescription = null,
                        tint = Color(0xFF10B981),
                        modifier = Modifier.size(64.dp)
                    )
                    Text("完成！", fontSize = 20.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

@Composable
private fun ReadyControls(onStartRecording: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        IconButton(
            onClick = onStartRecording,
            modifier = Modifier
                .size(64.dp)
                .background(Color(0xFFEF4444), CircleShape)
        ) {
            Icon(
                Icons.Default.Mic,
                contentDescription = "开始录音",
                tint = Color.White,
                modifier = Modifier.size(28.dp)
            )
        }
        Spacer(modifier = Modifier.height(6.dp))
        Text("点击开始录音 · 20秒~5分钟", fontSize = 12.sp, color = Color.Gray)
    }
}

@Composable
private fun RecordingControls(
    elapsedTime: Long,
    canStop: Boolean,
    onStop: () -> Unit
) {
    val minutes = elapsedTime / 60
    val seconds = elapsedTime % 60
    val timeStr = String.format(Locale.US, "%02d:%02d", minutes, seconds)

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        // Timer
        Text(
            text = "⏺ 正在录音  $timeStr",
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFFDC2626)
        )
        Spacer(modifier = Modifier.height(12.dp))

        // Stop button
        IconButton(
            onClick = { if (canStop) onStop() },
            modifier = Modifier
                .size(56.dp)
                .background(if (canStop) Color(0xFFDC2626) else Color.Gray, CircleShape)
        ) {
            Icon(
                Icons.Default.Stop,
                contentDescription = "停止",
                tint = Color.White,
                modifier = Modifier.size(24.dp)
            )
        }
        Spacer(modifier = Modifier.height(6.dp))
        if (canStop) {
            Text("点击停止", fontSize = 12.sp, color = Color(0xFFDC2626))
        } else {
            Text("还需录制 ${20 - elapsedTime} 秒", fontSize = 12.sp, color = Color(0xFFF59E0B))
        }
    }
}

@Composable
private fun RecordedControls(
    duration: Float,
    context: Context,
    audioFile: File?,
    mediaPlayer: MediaPlayer?,
    isPlaying: Boolean,
    playbackPosition: Float,
    onPlayPause: () -> Unit,
    onReRecord: () -> Unit,
    onSubmit: () -> Unit
) {
    val minutes = (duration / 60).toInt()
    val seconds = (duration % 60).toInt()
    val durationStr = String.format(Locale.US, "%02d:%02d", minutes, seconds)

    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(
            "✓ 录音完成 · 时长 $durationStr",
            fontSize = 14.sp,
            fontWeight = FontWeight.Bold,
            color = Color(0xFF16A34A)
        )
        Spacer(modifier = Modifier.height(12.dp))

        // Playback controls
        Card(
            modifier = Modifier.fillMaxWidth(),
            colors = CardDefaults.cardColors(containerColor = Color.White)
        ) {
            Row(
                modifier = Modifier.padding(14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(
                    onClick = onPlayPause,
                    modifier = Modifier
                        .size(36.dp)
                        .background(Color(0xFF10B981), CircleShape)
                ) {
                    Icon(
                        if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                        contentDescription = if (isPlaying) "暂停" else "播放",
                        tint = Color.White,
                        modifier = Modifier.size(18.dp)
                    )
                }
                Spacer(modifier = Modifier.width(12.dp))
                Column(modifier = Modifier.weight(1f)) {
                    LinearProgressIndicator(
                        progress = { playbackPosition },
                        modifier = Modifier.fillMaxWidth(),
                        color = Color(0xFF10B981)
                    )
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("0:00", fontSize = 11.sp, color = Color.Gray)
                        Text(durationStr, fontSize = 11.sp, color = Color.Gray)
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        // Action buttons
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedButton(
                onClick = onReRecord,
                modifier = Modifier.weight(1f)
            ) {
                Icon(Icons.Default.Refresh, contentDescription = null, modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(4.dp))
                Text("重录")
            }
            Button(
                onClick = onSubmit,
                modifier = Modifier.weight(2f),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF10B981))
            ) {
                Text("✓ 提交完成", fontWeight = FontWeight.SemiBold)
            }
        }

        Spacer(modifier = Modifier.height(8.dp))
        Text("提交后任务自动完成，家长可在进度页回听", fontSize = 12.sp, color = Color.Gray)
    }
}

private fun startRecording(context: Context, outputFile: File): MediaRecorder {
    return (if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        MediaRecorder(context)
    } else {
        @Suppress("DEPRECATION")
        MediaRecorder()
    }).apply {
        setAudioSource(MediaRecorder.AudioSource.MIC)
        setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
        setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
        setAudioEncodingBitRate(128000)
        setAudioSamplingRate(44100)
        setOutputFile(outputFile.absolutePath)
        prepare()
        start()
    }
}

private suspend fun submitRecording(
    context: Context,
    taskId: Int,
    audioFile: File,
    duration: Float
): String? = withContext(Dispatchers.IO) {
    try {
        val audioBody = audioFile.asRequestBody("audio/mp4".toMediaTypeOrNull())
        val audioPart = MultipartBody.Part.createFormData("audio", audioFile.name, audioBody)
        val durationBody = duration.toString().toRequestBody("text/plain".toMediaTypeOrNull())

        val response = RetrofitInstance.getApi(context).uploadRecording(taskId, audioPart, durationBody)
        if (response.isSuccessful) {
            null // success, no error message
        } else {
            val errorBody = response.errorBody()?.string()
            try {
                val json = org.json.JSONObject(errorBody ?: "")
                json.optString("detail", "提交失败 (${response.code()})")
            } catch (_: Exception) {
                "提交失败 (${response.code()})"
            }
        }
    } catch (e: Exception) {
        "提交失败: ${e.message}"
    }
}
