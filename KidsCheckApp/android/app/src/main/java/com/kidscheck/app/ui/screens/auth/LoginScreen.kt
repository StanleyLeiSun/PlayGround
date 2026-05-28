package com.kidscheck.app.ui.screens.auth

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.data.model.LoginRequest
import com.kidscheck.app.ui.theme.*
import com.kidscheck.app.util.TokenManager
import kotlinx.coroutines.launch

@Composable
fun LoginScreen(onLoginSuccess: () -> Unit) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var selectedUser by remember { mutableStateOf("") }
    var password by remember { mutableStateOf("") }
    var error by remember { mutableStateOf<String?>(null) }
    var loading by remember { mutableStateOf(false) }

    val users = listOf("爸爸", "妈妈", "爷爷", "奶奶", "姥姥", "姥爷")

    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(24.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        Text(
            "KidsCheck",
            fontSize = 32.sp,
            fontWeight = FontWeight.Bold,
            color = Primary
        )
        Text(
            "学习打卡助手",
            fontSize = 16.sp,
            color = TextSecondary,
            modifier = Modifier.padding(bottom = 32.dp)
        )

        Text("选择用户", fontSize = 16.sp, fontWeight = FontWeight.Medium,
            modifier = Modifier.fillMaxWidth().padding(bottom = 8.dp))

        // User grid
        Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                users.take(3).forEach { user ->
                    UserChip(user, selectedUser == user) { selectedUser = user }
                }
            }
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp), modifier = Modifier.fillMaxWidth()) {
                users.drop(3).forEach { user ->
                    UserChip(user, selectedUser == user) { selectedUser = user }
                }
            }
        }

        Spacer(modifier = Modifier.height(24.dp))

        OutlinedTextField(
            value = password,
            onValueChange = { password = it },
            label = { Text("密码") },
            visualTransformation = PasswordVisualTransformation(),
            singleLine = true,
            modifier = Modifier.fillMaxWidth().semantics { contentDescription = "login_password_field" }
        )

        if (error != null) {
            Text(error!!, color = Danger, fontSize = 14.sp, modifier = Modifier.padding(top = 8.dp).semantics { contentDescription = "login_error_text" })
        }

        Spacer(modifier = Modifier.height(24.dp))

        Button(
            onClick = {
                if (selectedUser.isEmpty()) {
                    error = "请选择用户"
                    return@Button
                }
                loading = true
                error = null
                scope.launch {
                    try {
                        val api = RetrofitInstance.getApi(context)
                        val resp = api.login(LoginRequest(selectedUser, password))
                        if (resp.isSuccessful) {
                            val body = resp.body()!!
                            TokenManager.saveToken(context, body.accessToken, body.user.username, body.user.role, body.user.id)
                            onLoginSuccess()
                        } else {
                            error = "密码错误"
                        }
                    } catch (e: Exception) {
                        error = "网络错误: ${e.message}"
                    } finally {
                        loading = false
                    }
                }
            },
            enabled = !loading && selectedUser.isNotEmpty(),
            modifier = Modifier.fillMaxWidth().height(52.dp).semantics { contentDescription = "login_button" },
            shape = RoundedCornerShape(14.dp),
            colors = ButtonDefaults.buttonColors(containerColor = Primary)
        ) {
            if (loading) CircularProgressIndicator(modifier = Modifier.size(24.dp).semantics { contentDescription = "login_loading_indicator" }, color = androidx.compose.ui.graphics.Color.White, strokeWidth = 2.dp)
            else Text("登录", fontSize = 18.sp, fontWeight = FontWeight.SemiBold)
        }
    }
}

@Composable
fun UserChip(name: String, selected: Boolean, onClick: () -> Unit) {
    Surface(
        modifier = Modifier
            .semantics { contentDescription = "login_user_chip_$name" }
            .clickable(onClick = onClick)
            .width(100.dp),
        shape = RoundedCornerShape(12.dp),
        color = if (selected) Primary else GrayLight,
        border = if (selected) null else ButtonDefaults.outlinedButtonBorder
    ) {
        Text(
            name,
            modifier = Modifier.padding(vertical = 12.dp, horizontal = 8.dp),
            color = if (selected) androidx.compose.ui.graphics.Color.White else TextPrimary,
            fontWeight = FontWeight.Medium,
            fontSize = 16.sp
        )
    }
}
