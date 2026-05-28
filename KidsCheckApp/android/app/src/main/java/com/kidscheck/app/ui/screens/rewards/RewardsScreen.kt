@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.kidscheck.app.ui.screens.rewards

import android.Manifest
import android.content.pm.PackageManager
import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.core.content.FileProvider
import coil.compose.AsyncImage
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.*
import com.kidscheck.app.ui.theme.*
import com.kidscheck.app.util.PhotoCompressor
import com.kidscheck.app.util.TokenManager
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File

@Composable
fun RewardsScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var rewards by remember { mutableStateOf<List<Reward>>(emptyList()) }
    var children by remember { mutableStateOf<List<Child>>(emptyList()) }
    var pointsMap by remember { mutableStateOf<Map<Int, Int>>(emptyMap()) }
    var redemptions by remember { mutableStateOf<List<RewardRedemption>>(emptyList()) }
    var showAddDialog by remember { mutableStateOf(false) }
    var showRedeemSheet by remember { mutableStateOf(false) }
    var selectedReward by remember { mutableStateOf<Reward?>(null) }
    var previewPhotoUrl by remember { mutableStateOf<String?>(null) }
    val isParent = TokenManager.getRole(context) == "parent"

    fun reload() {
        scope.launch {
            try {
                val api = RetrofitInstance.getApi(context)
                val rResp = api.getRewards()
                if (rResp.isSuccessful) rewards = rResp.body() ?: emptyList()
                val cResp = api.getChildren()
                if (cResp.isSuccessful) {
                    children = cResp.body() ?: emptyList()
                    children.forEach { child ->
                        val pResp = api.getPoints(child.id)
                        if (pResp.isSuccessful) pointsMap = pointsMap + (child.id to (pResp.body()?.balance ?: 0))
                    }
                }
                val rdResp = api.getRedemptions()
                if (rdResp.isSuccessful) redemptions = rdResp.body() ?: emptyList()
            } catch (_: Exception) {}
        }
    }

    LaunchedEffect(Unit) { reload() }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("积分兑换", fontWeight = FontWeight.Bold) },
                navigationIcon = { IconButton(onClick = onBack) { Icon(Icons.Default.ArrowBack, "返回") } }
            )
        },
        floatingActionButton = {
            if (isParent) {
                FloatingActionButton(onClick = { showAddDialog = true }, containerColor = Primary, modifier = Modifier.semantics { contentDescription = "reward_add_fab" }) {
                    Icon(Icons.Default.Add, "添加奖励", tint = androidx.compose.ui.graphics.Color.White)
                }
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier.padding(padding).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            // Points display
            item {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    children.forEach { child ->
                        Surface(shape = RoundedCornerShape(12.dp), color = PrimaryLight) {
                            Text(
                                "${child.nickname}: ${pointsMap[child.id] ?: 0}分",
                                modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp),
                                fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = Primary
                            )
                        }
                    }
                }
            }

            item { Text("🎁 可兑换奖励", fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = TextSecondary) }

            items(rewards) { reward ->
                Surface(
                    shape = RoundedCornerShape(16.dp),
                    border = androidx.compose.foundation.BorderStroke(2.dp, Border),
                    modifier = Modifier.semantics { contentDescription = "reward_item_${reward.id}" }
                ) {
                    Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(reward.title, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                            Text("需要 ${reward.costPoints} 积分", fontSize = 14.sp, color = TextSecondary)
                        }
                        if (isParent) {
                            Button(
                                onClick = {
                                    selectedReward = reward
                                    showRedeemSheet = true
                                },
                                colors = ButtonDefaults.buttonColors(containerColor = Primary),
                                contentPadding = PaddingValues(horizontal = 12.dp, vertical = 4.dp)
                            ) {
                                Text("兑换")
                            }
                            Spacer(modifier = Modifier.width(8.dp))
                            IconButton(onClick = {
                                scope.launch {
                                    RetrofitInstance.getApi(context).deleteReward(reward.id)
                                    reload()
                                }
                            }) {
                                Icon(Icons.Default.Delete, "删除", tint = Danger)
                            }
                        }
                    }
                }
            }

            // Redemption history
            if (redemptions.isNotEmpty()) {
                item {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("📋 兑换记录", fontSize = 16.sp, fontWeight = FontWeight.SemiBold, color = TextSecondary)
                }
                items(redemptions) { item ->
                    Surface(
                        shape = RoundedCornerShape(12.dp),
                        border = androidx.compose.foundation.BorderStroke(1.dp, Border)
                    ) {
                        Row(
                            modifier = Modifier.padding(12.dp).fillMaxWidth(),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            if (item.photoUrl != null) {
                                AsyncImage(
                                    model = "${RetrofitInstance.effectiveBaseUrl()}${item.photoUrl.removePrefix("/")}",
                                    contentDescription = null,
                                    modifier = Modifier.size(48.dp).clip(RoundedCornerShape(8.dp))
                                        .clickable { previewPhotoUrl = item.photoUrl },
                                    contentScale = ContentScale.Crop
                                )
                            } else {
                                Surface(
                                    modifier = Modifier.size(48.dp),
                                    shape = RoundedCornerShape(8.dp),
                                    color = PrimaryLight
                                ) {
                                    Box(contentAlignment = Alignment.Center) {
                                        Icon(Icons.Default.CardGiftcard, null, tint = Primary, modifier = Modifier.size(24.dp))
                                    }
                                }
                            }
                            Spacer(modifier = Modifier.width(12.dp))
                            Column(modifier = Modifier.weight(1f)) {
                                Text(item.rewardTitle ?: "奖励", fontSize = 15.sp, fontWeight = FontWeight.Medium)
                                Text(
                                    "${item.childName ?: ""} · ${item.redeemedAt.take(10)}",
                                    fontSize = 13.sp, color = TextSecondary
                                )
                            }
                            Text("-${item.pointsSpent}分", fontSize = 14.sp, fontWeight = FontWeight.Bold, color = Danger)
                        }
                    }
                }
            }
        }
    }

    // Add reward dialog
    if (showAddDialog) {
        var title by remember { mutableStateOf("") }
        var cost by remember { mutableStateOf("") }
        var desc by remember { mutableStateOf("") }

        AlertDialog(
            onDismissRequest = { showAddDialog = false },
            title = { Text("添加奖励") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = title, onValueChange = { title = it }, label = { Text("名称") }, singleLine = true, modifier = Modifier.semantics { contentDescription = "reward_add_title" })
                    OutlinedTextField(value = cost, onValueChange = { cost = it }, label = { Text("所需积分") }, singleLine = true, modifier = Modifier.semantics { contentDescription = "reward_add_cost" })
                    OutlinedTextField(value = desc, onValueChange = { desc = it }, label = { Text("描述") }, singleLine = true)
                }
            },
            confirmButton = {
                TextButton(onClick = {
                    if (title.isNotBlank() && cost.isNotBlank()) {
                        scope.launch {
                            try {
                                RetrofitInstance.getApi(context).createReward(
                                    RewardCreate(title, cost.toIntOrNull() ?: 10, desc.ifBlank { null })
                                )
                                showAddDialog = false
                                reload()
                            } catch (_: Exception) {}
                        }
                    }
                }) { Text("添加") }
            },
            dismissButton = { TextButton(onClick = { showAddDialog = false }) { Text("取消") } }
        )
    }

    // Redeem bottom sheet
    if (showRedeemSheet && selectedReward != null) {
        RedeemBottomSheet(
            reward = selectedReward!!,
            children = children,
            pointsMap = pointsMap,
            onDismiss = { showRedeemSheet = false },
            onRedeemed = {
                showRedeemSheet = false
                reload()
            }
        )
    }

    // Photo preview dialog
    if (previewPhotoUrl != null) {
        AlertDialog(
            onDismissRequest = { previewPhotoUrl = null },
            confirmButton = { TextButton(onClick = { previewPhotoUrl = null }) { Text("关闭") } },
            text = {
                AsyncImage(
                    model = "${RetrofitInstance.effectiveBaseUrl()}${previewPhotoUrl!!.removePrefix("/")}",
                    contentDescription = null,
                    modifier = Modifier.fillMaxWidth().aspectRatio(1f).clip(RoundedCornerShape(8.dp)),
                    contentScale = ContentScale.Fit
                )
            }
        )
    }
}

@Composable
fun RedeemBottomSheet(
    reward: Reward,
    children: List<Child>,
    pointsMap: Map<Int, Int>,
    onDismiss: () -> Unit,
    onRedeemed: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var selectedChild by remember { mutableStateOf(children.firstOrNull()) }
    var photoBytes by remember { mutableStateOf<ByteArray?>(null) }
    var photoFileName by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }
    var photoFile by remember { mutableStateOf<File?>(null) }
    var photoUri by remember { mutableStateOf<Uri?>(null) }

    val cameraLauncher = rememberLauncherForActivityResult(ActivityResultContracts.TakePicture()) { success ->
        if (success && photoFile != null) {
            photoBytes = PhotoCompressor.compressFile(photoFile!!)
            photoFileName = photoFile!!.name
        }
    }

    val galleryLauncher = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        if (uri != null) {
            photoBytes = PhotoCompressor.compressPhoto(context, uri)
            photoFileName = "gallery_${System.currentTimeMillis()}.jpg"
        }
    }

    val cameraPermissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        if (granted) {
            photoUri?.let { cameraLauncher.launch(it) }
        }
    }

    ModalBottomSheet(onDismissRequest = onDismiss) {
        Column(
            modifier = Modifier.padding(24.dp).fillMaxWidth(),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("兑换「${reward.title}」", fontSize = 20.sp, fontWeight = FontWeight.Bold)
            Text("消耗 ${reward.costPoints} 积分", fontSize = 14.sp, color = TextSecondary)
            Spacer(modifier = Modifier.height(20.dp))

            // Child selector
            if (children.size > 1) {
                Text("选择孩子", fontSize = 14.sp, color = TextSecondary)
                Spacer(modifier = Modifier.height(8.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    children.forEach { child ->
                        FilterChip(
                            selected = selectedChild?.id == child.id,
                            onClick = { selectedChild = child },
                            label = { Text(child.nickname) }
                        )
                    }
                }
                Spacer(modifier = Modifier.height(16.dp))
            }

            // Points info
            selectedChild?.let { child ->
                val balance = pointsMap[child.id] ?: 0
                val after = balance - reward.costPoints
                Surface(shape = RoundedCornerShape(12.dp), color = PrimaryLight, modifier = Modifier.fillMaxWidth()) {
                    Row(modifier = Modifier.padding(12.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("${child.nickname}当前积分", fontSize = 14.sp)
                        Text("$balance → $after", fontSize = 14.sp, fontWeight = FontWeight.Bold,
                            color = if (after >= 0) Primary else Danger)
                    }
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Photo section
            if (photoBytes != null) {
                Surface(shape = RoundedCornerShape(8.dp), color = SuccessLight, modifier = Modifier.fillMaxWidth()) {
                    Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.CheckCircle, null, tint = Success, modifier = Modifier.size(20.dp))
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("已选择照片", fontSize = 14.sp, color = Success)
                    }
                }
            } else {
                Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    OutlinedButton(onClick = {
                        val file = File(context.externalCacheDir, "reward_${System.currentTimeMillis()}.jpg")
                        photoFile = file
                        val uri = FileProvider.getUriForFile(context, "${context.packageName}.fileprovider", file)
                        photoUri = uri
                        if (ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
                            cameraLauncher.launch(uri)
                        } else {
                            cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                        }
                    }) {
                        Icon(Icons.Default.CameraAlt, null, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("拍照留底")
                    }
                    OutlinedButton(onClick = { galleryLauncher.launch("image/*") }) {
                        Icon(Icons.Default.PhotoLibrary, null, modifier = Modifier.size(18.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text("从相册")
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))

            val canRedeem = selectedChild != null && (pointsMap[selectedChild!!.id] ?: 0) >= reward.costPoints
            Button(
                onClick = {
                    if (selectedChild == null) return@Button
                    loading = true
                    scope.launch {
                        try {
                            val api = RetrofitInstance.getApi(context)
                            val childIdBody = selectedChild!!.id.toString()
                                .toRequestBody("text/plain".toMediaTypeOrNull())
                            val photoPart = if (photoBytes != null && photoFileName != null) {
                                MultipartBody.Part.createFormData(
                                    "photo", photoFileName!!,
                                    photoBytes!!.toRequestBody("image/jpeg".toMediaTypeOrNull())
                                )
                            } else null
                            val resp = api.redeemReward(reward.id, childIdBody, photoPart)
                            if (resp.isSuccessful) {
                                withContext(Dispatchers.Main) { Toast.makeText(context, "兑换成功！", Toast.LENGTH_SHORT).show() }
                                onRedeemed()
                            } else {
                                withContext(Dispatchers.Main) { Toast.makeText(context, "兑换失败：积分不足", Toast.LENGTH_SHORT).show() }
                            }
                        } catch (e: Exception) {
                            withContext(Dispatchers.Main) { Toast.makeText(context, "兑换失败: ${e.message}", Toast.LENGTH_SHORT).show() }
                        } finally {
                            loading = false
                        }
                    }
                },
                enabled = canRedeem && !loading,
                modifier = Modifier.fillMaxWidth().height(52.dp).semantics { contentDescription = "reward_redeem_confirm" },
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Primary)
            ) {
                if (loading) {
                    CircularProgressIndicator(modifier = Modifier.size(20.dp), color = androidx.compose.ui.graphics.Color.White, strokeWidth = 2.dp)
                } else {
                    Text("确认兑换", fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                }
            }

            Spacer(modifier = Modifier.height(12.dp))
            TextButton(onClick = onDismiss) { Text("取消", color = Gray) }
        }
    }
}
