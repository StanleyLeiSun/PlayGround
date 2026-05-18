package com.kidscheck.app.ui.screens.rewards

import android.widget.Toast
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.*
import com.kidscheck.app.ui.theme.*
import com.kidscheck.app.util.TokenManager
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun RewardsScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var rewards by remember { mutableStateOf<List<Reward>>(emptyList()) }
    var children by remember { mutableStateOf<List<Child>>(emptyList()) }
    var pointsMap by remember { mutableStateOf<Map<Int, Int>>(emptyMap()) }
    var showAddDialog by remember { mutableStateOf(false) }
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
                FloatingActionButton(onClick = { showAddDialog = true }, containerColor = Primary) {
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
                    border = androidx.compose.foundation.BorderStroke(2.dp, Border)
                ) {
                    Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(reward.title, fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
                            Text("需要 ${reward.costPoints} 积分", fontSize = 14.sp, color = TextSecondary)
                        }
                        if (isParent) {
                            IconButton(onClick = {
                                scope.launch {
                                    RetrofitInstance.getApi(context).deleteReward(reward.id)
                                    reload()
                                }
                            }) {
                                Icon(Icons.Default.Delete, "删除", tint = Danger)
                            }
                        } else {
                            // Redeem button for first child (simplified)
                            val child = children.firstOrNull()
                            val balance = child?.let { pointsMap[it.id] ?: 0 } ?: 0
                            Button(
                                onClick = {
                                    if (child != null) {
                                        scope.launch {
                                            try {
                                                val resp = RetrofitInstance.getApi(context).redeemReward(reward.id, child.id)
                                                if (resp.isSuccessful) {
                                                    Toast.makeText(context, "兑换成功！", Toast.LENGTH_SHORT).show()
                                                    reload()
                                                } else {
                                                    Toast.makeText(context, "积分不足", Toast.LENGTH_SHORT).show()
                                                }
                                            } catch (_: Exception) {}
                                        }
                                    }
                                },
                                enabled = balance >= reward.costPoints,
                                colors = ButtonDefaults.buttonColors(
                                    containerColor = if (balance >= reward.costPoints) Primary else Gray
                                )
                            ) {
                                Text("兑换")
                            }
                        }
                    }
                }
            }
        }
    }

    if (showAddDialog) {
        var title by remember { mutableStateOf("") }
        var cost by remember { mutableStateOf("") }
        var desc by remember { mutableStateOf("") }

        AlertDialog(
            onDismissRequest = { showAddDialog = false },
            title = { Text("添加奖励") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = title, onValueChange = { title = it }, label = { Text("名称") }, singleLine = true)
                    OutlinedTextField(value = cost, onValueChange = { cost = it }, label = { Text("所需积分") }, singleLine = true)
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
}
