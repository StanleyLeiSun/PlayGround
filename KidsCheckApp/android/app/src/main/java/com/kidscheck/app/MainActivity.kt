package com.kidscheck.app

import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.lifecycleScope
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.AppVersion
import com.kidscheck.app.ui.screens.auth.LoginScreen
import com.kidscheck.app.ui.screens.home.MainScreen
import com.kidscheck.app.ui.screens.rewards.RewardsScreen
import com.kidscheck.app.ui.screens.template.TemplateManagementScreen
import com.kidscheck.app.ui.screens.update.UpdateDialog
import com.kidscheck.app.util.ApkDownloader
import com.kidscheck.app.util.AuthEvent
import com.kidscheck.app.util.AuthEventBus
import com.kidscheck.app.util.TokenManager
import com.kidscheck.app.util.VersionChecker
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    private var pendingVersion by mutableStateOf<AppVersion?>(null)
    private var isDownloading by mutableStateOf(false)
    private var downloadProgress by mutableStateOf(0)

    // 全局导航控制器引用，用于处理 Token 过期
    internal var navControllerRef: androidx.navigation.NavController? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 注册下载完成回调
        ApkDownloader.registerReceiver(
            context = this,
            onComplete = { localUri ->
                isDownloading = false
                if (localUri.isNotEmpty()) {
                    val file = java.io.File(android.net.Uri.parse(localUri).path ?: "")
                    if (file.exists()) {
                        com.kidscheck.app.util.ApkInstaller.installApk(this, file)
                    }
                }
                pendingVersion = null
            },
            onProgress = { progress ->
                downloadProgress = progress
            }
        )

        setContent {
            KidsCheckNavHost()

            // 显示更新对话框
            val version = pendingVersion
            if (version != null) {
                UpdateDialog(
                    version = version,
                    isDownloading = isDownloading,
                    downloadProgress = downloadProgress,
                    onUpdateClick = {
                        isDownloading = true
                        downloadProgress = 0
                        ApkDownloader.startDownload(this@MainActivity, version)
                    },
                    onSkipClick = if (VersionChecker.isForceUpdate(version)) null else {
                        { pendingVersion = null }
                    },
                    onDismiss = { pendingVersion = null }
                )
            }
        }

        // 检查更新
        checkForUpdate()

        // 监听 Token 过期事件
        observeAuthEvents()
    }

    override fun onDestroy() {
        super.onDestroy()
        ApkDownloader.unregisterReceiver(this)
    }

    private fun checkForUpdate() {
        lifecycleScope.launch {
            val version = VersionChecker.checkForUpdate(this@MainActivity)
            if (version != null) {
                pendingVersion = version
            }
        }
    }

    private fun observeAuthEvents() {
        lifecycleScope.launch {
            AuthEventBus.authEvents.collect { event ->
                when (event) {
                    is AuthEvent.TokenExpired -> {
                        Toast.makeText(this@MainActivity, "登录已过期，请重新登录", Toast.LENGTH_SHORT).show()
                        navControllerRef?.let { nav ->
                            TokenManager.clear(this@MainActivity)
                            nav.navigate("login") {
                                popUpTo("main") { inclusive = true }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun KidsCheckNavHost() {
    val navController = rememberNavController()
    val context = LocalContext.current
    val activity = context as? MainActivity
    var isValidating by remember { mutableStateOf(true) }
    var startDest by remember { mutableStateOf("login") }

    // 启动时验证 Token 有效性
    LaunchedEffect(Unit) {
        if (TokenManager.isLoggedIn(context)) {
            try {
                val api = RetrofitInstance.getApi(context)
                val resp = api.getMe()
                if (resp.isSuccessful) {
                    startDest = "main"
                } else {
                    // Token 无效，清除
                    TokenManager.clear(context)
                }
            } catch (e: Exception) {
                // 网络错误等情况，仍然允许进入（可能离线使用）
                startDest = "main"
            }
        }
        isValidating = false
    }

    // 设置 navController 引用给 MainActivity
    LaunchedEffect(navController) {
        activity?.navControllerRef = navController
    }

    if (!isValidating) {
        NavHost(navController = navController, startDestination = startDest) {
            composable("login") {
                LoginScreen(onLoginSuccess = {
                    navController.navigate("main") {
                        popUpTo("login") { inclusive = true }
                    }
                })
            }
            composable("main") {
                MainScreen(
                    onNavigateToTemplates = { navController.navigate("templates") },
                    onNavigateToRewards = { navController.navigate("rewards") },
                    onLogout = {
                        TokenManager.clear(context)
                        navController.navigate("login") {
                            popUpTo("main") { inclusive = true }
                        }
                    }
                )
            }
            composable("templates") {
                TemplateManagementScreen(onBack = { navController.popBackStack() })
            }
            composable("rewards") {
                RewardsScreen(onBack = { navController.popBackStack() })
            }
        }
    } else {
        // 验证中显示加载界面
        Box(
            modifier = Modifier.fillMaxSize(),
            contentAlignment = Alignment.Center
        ) {
            CircularProgressIndicator()
        }
    }
}
