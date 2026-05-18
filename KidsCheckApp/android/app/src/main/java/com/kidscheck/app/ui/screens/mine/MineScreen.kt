package com.kidscheck.app.ui.screens.mine

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.Child
import com.kidscheck.app.data.model.PointBalance
import com.kidscheck.app.ui.theme.*
import com.kidscheck.app.util.TokenManager
import kotlinx.coroutines.launch

@Composable
fun MineScreen(
    isParent: Boolean,
    onNavigateToTemplates: () -> Unit,
    onNavigateToRewards: () -> Unit,
    onLogout: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var children by remember { mutableStateOf<List<Child>>(emptyList()) }
    var pointsMap by remember { mutableStateOf<Map<Int, Int>>(emptyMap()) }
    val username = TokenManager.getUsername(context) ?: ""

    LaunchedEffect(Unit) {
        scope.launch {
            try {
                val api = RetrofitInstance.getApi(context)
                val childResp = api.getChildren()
                if (childResp.isSuccessful) {
                    children = childResp.body() ?: emptyList()
                    children.forEach { child ->
                        val ptsResp = api.getPoints(child.id)
                        if (ptsResp.isSuccessful) {
                            pointsMap = pointsMap + (child.id to (ptsResp.body()?.balance ?: 0))
                        }
                    }
                }
            } catch (_: Exception) {}
        }
    }

    LazyColumn(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        // Profile card
        item {
            Surface(
                shape = RoundedCornerShape(20.dp),
                modifier = Modifier.fillMaxWidth()
            ) {
                Box(modifier = Modifier.background(Brush.horizontalGradient(listOf(Primary, Color(0xFFFFB74D)))).padding(24.dp)) {
                    Column {
                        Text("🏠 萝卜蚕豆之家", fontSize = 20.sp, fontWeight = FontWeight.Bold, color = Color.White)
                        Spacer(modifier = Modifier.height(16.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                            children.forEach { child ->
                                Surface(shape = RoundedCornerShape(12.dp), color = Color.White.copy(alpha = 0.2f)) {
                                    Column(
                                        modifier = Modifier.padding(12.dp),
                                        horizontalAlignment = Alignment.CenterHorizontally
                                    ) {
                                        Text(child.nickname, fontSize = 14.sp, color = Color.White)
                                        Text("${pointsMap[child.id] ?: 0}分", fontSize = 22.sp, fontWeight = FontWeight.Bold, color = Color.White)
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // Menu items
        item { MenuItem(Icons.Default.CardGiftcard, "积分兑换") { onNavigateToRewards() } }
        if (isParent) {
            item { MenuItem(Icons.Default.EditNote, "任务模板管理", "父母") { onNavigateToTemplates() } }
            item { MenuItem(Icons.Default.EmojiEvents, "奖励库管理", "父母") { onNavigateToRewards() } }
        }
        item { MenuItem(Icons.Default.Settings, "设置") {} }
        item {
            Surface(
                modifier = Modifier.fillMaxWidth().clickable { onLogout() },
                shape = RoundedCornerShape(14.dp),
                border = androidx.compose.foundation.BorderStroke(2.dp, Danger.copy(alpha = 0.3f)),
                color = Danger.copy(alpha = 0.05f)
            ) {
                Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Logout, contentDescription = null, tint = Danger, modifier = Modifier.size(24.dp))
                    Spacer(modifier = Modifier.width(14.dp))
                    Text("退出登录 ($username)", fontSize = 16.sp, fontWeight = FontWeight.Medium, color = Danger)
                }
            }
        }
    }
}

@Composable
fun MenuItem(icon: ImageVector, text: String, badge: String? = null, onClick: () -> Unit) {
    Surface(
        modifier = Modifier.fillMaxWidth().clickable(onClick = onClick),
        shape = RoundedCornerShape(14.dp),
        color = MaterialTheme.colorScheme.surface,
        border = androidx.compose.foundation.BorderStroke(2.dp, Border)
    ) {
        Row(modifier = Modifier.padding(16.dp), verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier.size(40.dp).background(PrimaryLight, RoundedCornerShape(10.dp)),
                contentAlignment = Alignment.Center
            ) {
                Icon(icon, contentDescription = null, tint = Primary, modifier = Modifier.size(24.dp))
            }
            Spacer(modifier = Modifier.width(14.dp))
            Text(text, fontSize = 16.sp, fontWeight = FontWeight.Medium, modifier = Modifier.weight(1f))
            if (badge != null) {
                Surface(shape = RoundedCornerShape(8.dp), color = PurpleLight) {
                    Text(badge, modifier = Modifier.padding(horizontal = 8.dp, vertical = 2.dp),
                        fontSize = 11.sp, color = Purple)
                }
                Spacer(modifier = Modifier.width(8.dp))
            }
            Icon(Icons.Default.ChevronRight, contentDescription = null, tint = Gray)
        }
    }
}
