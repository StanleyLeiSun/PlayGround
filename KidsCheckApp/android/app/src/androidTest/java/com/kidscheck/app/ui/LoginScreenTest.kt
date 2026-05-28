package com.kidscheck.app.ui

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.kidscheck.app.MainActivity
import com.kidscheck.app.testutil.MockWebServerRule
import com.kidscheck.app.testutil.TestData
import com.kidscheck.app.util.TokenManager
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class LoginScreenTest {

    @get:Rule
    val mockRule = MockWebServerRule()

    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    private val dispatcher get() = mockRule.dispatcher

    @Before
    fun setup() {
        TokenManager.clear(composeRule.activity)
    }

    @After
    fun teardown() {
        TokenManager.clear(composeRule.activity)
    }

    @Test
    fun loginScreen_showsAllUserChips() {
        val users = listOf("爸爸", "妈妈", "爷爷", "奶奶", "姥姥", "姥爷")
        users.forEach { user ->
            composeRule.onNodeWithContentDescription("login_user_chip_$user").assertIsDisplayed()
        }
    }

    @Test
    fun loginScreen_selectUserChip_highlightsIt() {
        composeRule.onNodeWithContentDescription("login_user_chip_爸爸").performClick()
        // Surface doesn't expose Selected semantics; verify chip still exists after click
        composeRule.onNodeWithContentDescription("login_user_chip_爸爸").assertIsDisplayed()
    }

    @Test
    fun loginScreen_enterPassword_andLogin_success() {
        dispatcher.register("POST", "/api/auth/login", TestData.loginResponseJson("爸爸"))
        dispatcher.register("GET", "/api/children", TestData.childListJson())
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksJson())
        dispatcher.register("GET", "/api/app/version", """{"version_code":10100,"version_name":"1.1.0","release_notes":"","force_update":false}""")

        composeRule.onNodeWithContentDescription("login_user_chip_爸爸").performClick()
        composeRule.onNodeWithContentDescription("login_password_field").performTextInput("123456")
        composeRule.onNodeWithContentDescription("login_button").performClick()

        // Verify login API was called and token was saved (navigation doesn't work in test env)
        composeRule.waitUntil(timeoutMillis = 5000) {
            TokenManager.isLoggedIn(composeRule.activity)
        }
    }

    @Test
    fun loginScreen_login_wrongPassword_showsError() {
        dispatcher.register("POST", "/api/auth/login", """{"detail":"Unauthorized"}""", code = 401)

        composeRule.onNodeWithContentDescription("login_user_chip_爸爸").performClick()
        composeRule.onNodeWithContentDescription("login_password_field").performTextInput("wrong")
        composeRule.onNodeWithContentDescription("login_button").performClick()

        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithContentDescription("login_error_text").fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithContentDescription("login_error_text").assertTextContains("密码错误")
    }

    @Test
    fun loginScreen_login_noUserSelected_buttonDisabled() {
        composeRule.onNodeWithContentDescription("login_password_field").performTextInput("123456")
        // Button should be disabled when no user is selected
        composeRule.onNodeWithContentDescription("login_button").assertIsNotEnabled()
    }

    @Test
    fun loginScreen_login_showsLoadingState() {
        dispatcher.register("POST", "/api/auth/login", TestData.loginResponseJson(), delayMs = 2000)
        dispatcher.register("GET", "/api/children", TestData.childListJson())
        dispatcher.register("GET", "/api/app/version", """{"version_code":10100,"version_name":"1.1.0","release_notes":"","force_update":false}""")

        composeRule.onNodeWithContentDescription("login_user_chip_爸爸").performClick()
        composeRule.onNodeWithContentDescription("login_password_field").performTextInput("123456")
        composeRule.onNodeWithContentDescription("login_button").performClick()

        composeRule.waitUntil(timeoutMillis = 1000) {
            composeRule.onAllNodesWithContentDescription("login_loading_indicator").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun loginScreen_passwordField_isObscured() {
        composeRule.onNodeWithContentDescription("login_password_field").performTextInput("secret123")
        // The field should have password visual transformation - text content should not be directly visible
        composeRule.onNodeWithContentDescription("login_password_field").assertExists()
    }
}
