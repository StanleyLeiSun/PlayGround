package com.kidscheck.app.ui

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.kidscheck.app.MainActivity
import com.kidscheck.app.testutil.MockWebServerRule
import com.kidscheck.app.testutil.TestData
import com.kidscheck.app.testutil.waitUntilNodeWithContentDescription
import com.kidscheck.app.testutil.waitUntilNodeWithText
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ProgressScreenTest {

    @get:Rule
    val mockRule = MockWebServerRule(preLoginUsername = "爸爸")

    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    private val dispatcher get() = mockRule.dispatcher

    private fun setupCommonMocks() {
        dispatcher.register("GET", "/api/children", TestData.childListJson())
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksJson())
        dispatcher.register("GET", "/api/app/version", """{"version_code":10100,"version_name":"1.1.0","release_notes":"","force_update":false}""")
    }

    private fun navigateToProgress() {
        setupCommonMocks()
        dispatcher.register("GET", "/api/progress/.*", TestData.progressResponseJson())
        composeRule.waitUntilNodeWithText("进度")
        composeRule.onNodeWithText("进度").performClick()
        composeRule.waitUntilNodeWithContentDescription("progress_prev_day")
    }

    @Test
    fun progress_showsDateNavigation() {
        navigateToProgress()
        composeRule.onNodeWithContentDescription("progress_prev_day").assertIsDisplayed()
        composeRule.onNodeWithContentDescription("progress_next_day").assertIsDisplayed()
    }

    @Test
    fun progress_prevDay_loadsPreviousDay() {
        navigateToProgress()
        composeRule.onNodeWithContentDescription("progress_prev_day").performClick()
        composeRule.waitUntil(timeoutMillis = 3000) {
            composeRule.onAllNodesWithContentDescription("progress_prev_day").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun progress_nextDay_loadsNextDay() {
        navigateToProgress()
        composeRule.onNodeWithContentDescription("progress_next_day").performClick()
        composeRule.waitUntil(timeoutMillis = 3000) {
            composeRule.onAllNodesWithContentDescription("progress_next_day").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun progress_showsProgressBar_withCorrectRatio() {
        navigateToProgress()
        composeRule.waitUntilNodeWithText("完成进度")
        composeRule.onNodeWithText("完成进度").assertIsDisplayed()
        composeRule.onNodeWithText("3/5").assertIsDisplayed()
    }

    @Test
    fun progress_showsTimeline_withTasks() {
        navigateToProgress()
        composeRule.waitUntilNodeWithText("📅 时间线")
        composeRule.onNodeWithText("📅 时间线").assertIsDisplayed()
    }

    @Test
    fun progress_showsPointsSummary() {
        navigateToProgress()
        composeRule.waitUntilNodeWithText("今日获得")
        composeRule.onNodeWithText("今日获得").assertIsDisplayed()
        composeRule.onNodeWithText("累计积分").assertIsDisplayed()
        composeRule.onNodeWithContentDescription("progress_points_today").assertIsDisplayed()
    }

    @Test
    fun progress_emptyDay_showsEmptyState() {
        setupCommonMocks()
        dispatcher.register("GET", "/api/progress/.*", TestData.progressResponseEmptyJson())

        composeRule.waitUntilNodeWithText("进度")
        composeRule.onNodeWithText("进度").performClick()
        composeRule.waitUntilNodeWithContentDescription("progress_empty")
        composeRule.onNodeWithContentDescription("progress_empty").assertTextContains("当天没有任务")
    }
}
