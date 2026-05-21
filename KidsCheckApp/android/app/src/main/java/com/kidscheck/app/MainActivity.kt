package com.kidscheck.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.*
import androidx.lifecycle.lifecycleScope
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.kidscheck.app.data.model.AppVersion
import com.kidscheck.app.ui.screens.auth.LoginScreen
import com.kidscheck.app.ui.screens.home.MainScreen
import com.kidscheck.app.ui.screens.rewards.RewardsScreen
import com.kidscheck.app.ui.screens.template.TemplateManagementScreen
import com.kidscheck.app.ui.screens.update.UpdateDialog
import com.kidscheck.app.util.ApkDownloader
import com.kidscheck.app.util.TokenManager
import com.kidscheck.app.util.VersionChecker
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    private var pendingVersion by mutableStateOf<AppVersion?>(null)
    private var isDownloading by mutableStateOf(false)
    private var downloadProgress by mutableStateOf(0)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // 注册下载完成回调
        ApkDownloader.registerReceiver(
            context = this,
            onComplete = { localUri ->
                isDownloading = false
                if (localUri.isNotEmpty()) {
                    // 下载完成，安装APK
                    val file = java.io.File(localUri)
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
}

@Composable
fun KidsCheckNavHost() {
    val navController = rememberNavController()
    val startDest = if (TokenManager.isLoggedIn(KidsCheckApp.instance)) "main" else "login"

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
                    TokenManager.clear(KidsCheckApp.instance)
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
}
