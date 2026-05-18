package com.kidscheck.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.runtime.Composable
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.kidscheck.app.ui.screens.auth.LoginScreen
import com.kidscheck.app.ui.screens.home.MainScreen
import com.kidscheck.app.ui.screens.template.TemplateManagementScreen
import com.kidscheck.app.ui.screens.rewards.RewardsScreen
import com.kidscheck.app.util.TokenManager

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            KidsCheckNavHost()
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
