package com.kidscheck.app.testutil

import androidx.test.platform.app.InstrumentationRegistry
import com.kidscheck.app.data.api.RetrofitInstance
import com.kidscheck.app.util.TokenManager
import okhttp3.mockwebserver.MockWebServer
import org.junit.rules.TestRule
import org.junit.runner.Description
import org.junit.runners.model.Statement

/**
 * JUnit TestRule that starts a MockWebServer and configures RetrofitInstance
 * to use it. Optionally pre-sets the auth token so the app starts directly
 * on the main screen (bypassing login UI).
 *
 * Common endpoints (version check, children list, daily tasks) are pre-registered
 * before the activity launches, so onCreate() and MainScreen LaunchedEffect get
 * 200 responses instead of 404.
 *
 * @param preLoginUsername If non-null, pre-set this user's token before the
 *   activity launches. The app will start on the main screen.
 * @param preLoginRole User role (default "parent")
 * @param preLoginUserId User ID (default 1)
 */
class MockWebServerRule(
    private val preLoginUsername: String? = null,
    private val preLoginRole: String = "parent",
    private val preLoginUserId: Int = 1
) : TestRule {
    val server = MockWebServer()
    val dispatcher = MockApiDispatcher()

    override fun apply(base: Statement, description: Description): Statement {
        return object : Statement() {
            override fun evaluate() {
                server.dispatcher = dispatcher
                server.start()
                RetrofitInstance.testBaseUrl = server.url("/").toString()

                // Pre-set token if configured. This runs before composeRule
                // creates the activity, so the app starts on the main screen.
                if (preLoginUsername != null) {
                    val context = InstrumentationRegistry.getInstrumentation().targetContext
                    TokenManager.saveToken(context, "test-jwt-token", preLoginUsername, preLoginRole, preLoginUserId)
                }

                // Pre-register common endpoints that the activity needs on startup.
                // checkForUpdate() in onCreate() calls GET /api/app/version.
                // MainScreen LaunchedEffect calls GET /api/children and TaskListScreen
                // calls GET /api/daily-tasks. Without these, the activity gets 404
                // responses and enters error/loading states.
                dispatcher.register("GET", "/api/app/version", """{"version_code":10105,"version_name":"1.1.5","release_notes":"","force_update":false}""")
                dispatcher.register("GET", "/api/children", TestData.childListJson())
                dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksJson())

                try {
                    base.evaluate()
                } finally {
                    RetrofitInstance.testBaseUrl = null
                    dispatcher.clear()
                    server.shutdown()
                    // Clean up token
                    val context = InstrumentationRegistry.getInstrumentation().targetContext
                    TokenManager.clear(context)
                }
            }
        }
    }
}
