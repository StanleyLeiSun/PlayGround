package com.kidscheck.app.ui.screens.home

import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.kidscheck.app.data.model.Child
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.ui.screens.progress.ProgressScreen
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
    val isParent = TokenManager.getRole(context) == "parent"

    LaunchedEffect(Unit) {
        scope.launch {
            try {
                val resp = RetrofitInstance.getApi(context).getChildren()
                if (resp.isSuccessful) {
                    children = resp.body() ?: emptyList()
                    selectedChild = children.firstOrNull()
                }
            } catch (_: Exception) {}
        }
    }

    val tabs = listOf("今日任务", "进度", "我的")
    val icons = listOf(Icons.Default.CheckCircle, Icons.Default.BarChart, Icons.Default.Person)

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
                                onClick = { selectedChild = child },
                                text = { Text(child.nickname, fontSize = 16.sp, fontWeight = FontWeight.Medium) }
                            )
                        }
                    }
                }
            }
        },
        bottomBar = {
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
    ) { padding ->
        Box(modifier = Modifier.padding(padding)) {
            when (currentTab) {
                0 -> selectedChild?.let {
                    TaskListScreen(childId = it.id, childName = it.nickname)
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
