package com.kidscheck.app.ui.screens.home

import android.widget.Toast
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kidscheck.app.data.model.Child
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.ui.screens.progress.ProgressScreen
import com.kidscheck.app.ui.screens.insights.DataInsightsScreen
import com.kidscheck.app.ui.screens.mine.MineScreen
import com.kidscheck.app.ui.theme.Primary
import com.kidscheck.app.ui.theme.TextSecondary
import com.kidscheck.app.util.TokenManager
import kotlinx.coroutines.launch

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(
    onNavigateToTemplates: () -> Unit,
    onNavigateToRewards: () -> Unit,
    onLogout: () -> Unit
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var currentTab by remember { mutableIntStateOf(0) }
    var children by remember { mutableStateOf<List<Child>>(emptyList()) }
    var selectedChild by remember { mutableStateOf<Child?>(null) }
    var childSwitchLocked by remember { mutableStateOf(false) }
    var isLoading by remember { mutableStateOf(true) }
    var errorMessage by remember { mutableStateOf<String?>(null) }
    val isParent = TokenManager.getRole(context) == "parent"

    LaunchedEffect(Unit) {
        scope.launch {
            try {
                val resp = RetrofitInstance.getApi(context).getChildren()
                if (resp.isSuccessful) {
                    children = resp.body() ?: emptyList()
                    selectedChild = children.firstOrNull()
                    errorMessage = null
                } else {
                    // API 返回错误（401 已在拦截器处理，这里处理其他错误）
                    errorMessage = "加载失败: ${resp.code()}"
                    Toast.makeText(context, "加载数据失败", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                // 网络错误等
                errorMessage = "网络错误: ${e.message}"
                Toast.makeText(context, "网络连接失败，请检查网络", Toast.LENGTH_SHORT).show()
            } finally {
                isLoading = false
            }
        }
    }

    val tabs = if (isParent) listOf("今日任务", "进度", "洞察", "我的") else listOf("今日任务", "进度", "我的")
    val icons = if (isParent) listOf(Icons.Default.CheckCircle, Icons.Default.BarChart, Icons.Default.Star, Icons.Default.Person) else listOf(Icons.Default.CheckCircle, Icons.Default.BarChart, Icons.Default.Person)

    Scaffold(
        topBar = {
            Column {
                TopAppBar(
                    title = { Text(tabs[currentTab], fontWeight = FontWeight.Bold, fontSize = 20.sp) },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.surface)
                )
                // Child tabs
                if (children.isNotEmpty()) {
                    TabRow(
                        selectedTabIndex = children.indexOf(selectedChild).coerceAtLeast(0),
                        containerColor = MaterialTheme.colorScheme.surface,
                        contentColor = Primary
                    ) {
                        children.forEach { child ->
                            Tab(
                                selected = selectedChild?.id == child.id,
                                onClick = { if (!childSwitchLocked) selectedChild = child },
                                enabled = !childSwitchLocked,
                                modifier = Modifier.semantics { contentDescription = "main_child_tab_${child.nickname}" },
                                text = { Text(child.nickname, fontSize = 16.sp, fontWeight = FontWeight.Medium) }
                            )
                        }
                    }
                }
            }
        },
        bottomBar = {
            if (!childSwitchLocked) {
                NavigationBar {
                    tabs.forEachIndexed { index, title ->
                        NavigationBarItem(
                            icon = { Icon(icons[index], contentDescription = title) },
                            label = { Text(title) },
                            selected = currentTab == index,
                            onClick = { currentTab = index }
                        )
                    }
                }
            }
        }
    ) { padding ->
        Box(modifier = Modifier.padding(padding)) {
            when {
                isLoading -> {
                    // 加载中状态
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            CircularProgressIndicator()
                            Spacer(modifier = Modifier.height(16.dp))
                            Text("加载中...", color = TextSecondary)
                        }
                    }
                }
                errorMessage != null && children.isEmpty() -> {
                    // 错误状态（只有在没有数据时才显示错误页面）
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(
                            horizontalAlignment = Alignment.CenterHorizontally,
                            modifier = Modifier.padding(16.dp)
                        ) {
                            Icon(
                                Icons.Default.Error,
                                contentDescription = "错误",
                                modifier = Modifier.size(48.dp),
                                tint = MaterialTheme.colorScheme.error
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                errorMessage!!,
                                color = TextSecondary,
                                style = MaterialTheme.typography.bodyLarge
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Button(onClick = {
                                isLoading = true
                                errorMessage = null
                                scope.launch {
                                    try {
                                        val resp = RetrofitInstance.getApi(context).getChildren()
                                        if (resp.isSuccessful) {
                                            children = resp.body() ?: emptyList()
                                            selectedChild = children.firstOrNull()
                                        } else {
                                            errorMessage = "加载失败: ${resp.code()}"
                                        }
                                    } catch (e: Exception) {
                                        errorMessage = "网络错误: ${e.message}"
                                    } finally {
                                        isLoading = false
                                    }
                                }
                            }) {
                                Text("重试")
                            }
                        }
                    }
                }
                else -> {
                    // 正常内容
                    if (isParent) {
                        when (currentTab) {
                            0 -> selectedChild?.let {
                                TaskListScreen(childId = it.id, childName = it.nickname, onOralPracticeChanged = { locked -> childSwitchLocked = locked })
                            }
                            1 -> selectedChild?.let {
                                ProgressScreen(childId = it.id)
                            }
                            2 -> selectedChild?.let {
                                DataInsightsScreen(childId = it.id)
                            }
                            3 -> MineScreen(
                                isParent = isParent,
                                onNavigateToTemplates = onNavigateToTemplates,
                                onNavigateToRewards = onNavigateToRewards,
                                onLogout = onLogout
                            )
                        }
                    } else {
                        when (currentTab) {
                            0 -> selectedChild?.let {
                                TaskListScreen(childId = it.id, childName = it.nickname, onOralPracticeChanged = { locked -> childSwitchLocked = locked })
                            }
                            1 -> selectedChild?.let {
                                ProgressScreen(childId = it.id)
                            }
                            2 -> MineScreen(
                                isParent = isParent,
                                onNavigateToTemplates = onNavigateToTemplates,
                                onNavigateToRewards = onNavigateToRewards,
                                onLogout = onLogout
                            )
                        }
                    }
                }
            }
        }
    }
}
