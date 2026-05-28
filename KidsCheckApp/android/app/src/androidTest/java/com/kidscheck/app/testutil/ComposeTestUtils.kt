package com.kidscheck.app.testutil

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.ComposeTestRule

fun ComposeTestRule.waitUntilNodeWithContentDescription(
    description: String,
    timeoutMillis: Long = 5000
) {
    waitUntil(timeoutMillis) {
        onAllNodesWithContentDescription(description).fetchSemanticsNodes().isNotEmpty()
    }
}

fun ComposeTestRule.waitUntilNodeWithText(
    text: String,
    substring: Boolean = false,
    timeoutMillis: Long = 5000
) {
    waitUntil(timeoutMillis) {
        if (substring) {
            onAllNodes(hasText(text, substring = true)).fetchSemanticsNodes().isNotEmpty()
        } else {
            onAllNodesWithText(text).fetchSemanticsNodes().isNotEmpty()
        }
    }
}

fun ComposeTestRule.setTextField(description: String, text: String) {
    onNodeWithContentDescription(description).performTextInput(text)
}

/**
 * Perform login via UI interactions. Use when testing login flow itself.
 * For tests that just need to be logged in, use directLogin() instead.
 */
fun ComposeTestRule.performLogin(
    dispatcher: MockApiDispatcher,
    username: String = "爸爸",
    password: String = "123456"
) {
    dispatcher.register("POST", "/api/auth/login", TestData.loginResponseJson(username))
    dispatcher.register("GET", "/api/children", TestData.childListJson())
    dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksJson())
    dispatcher.register("GET", "/api/app/version", """{"version_code": 10100, "version_name": "1.1.0", "release_notes": "", "force_update": false}""")

    waitUntilNodeWithContentDescription("login_user_chip_$username")
    onNodeWithContentDescription("login_user_chip_$username").performClick()
    onNodeWithContentDescription("login_password_field").performTextInput(password)
    onNodeWithContentDescription("login_button").performClick()

    waitUntilNodeWithText("今日任务", timeoutMillis = 10000)
}

/**
 * Set token directly in SharedPreferences so the app starts on the main screen.
 * This bypasses the login UI and is faster/more reliable for tests that don't
 * specifically test the login flow.
 */
fun directLogin(
    context: android.content.Context,
    username: String = "爸爸",
    role: String = "parent",
    userId: Int = 1
) {
    com.kidscheck.app.util.TokenManager.saveToken(context, "test-jwt-token", username, role, userId)
}
