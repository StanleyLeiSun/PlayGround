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
class DataInsightsScreenTest {

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

    private fun navigateToInsights() {
        setupCommonMocks()
        dispatcher.register("GET", "/api/insights/.*", TestData.insightsResponseJson())
        composeRule.waitUntilNodeWithText("洞察")
        composeRule.onNodeWithText("洞察").performClick()
        composeRule.waitUntilNodeWithContentDescription("insights_period_week")
    }

    @Test
    fun insights_showsPeriodSelector() {
        navigateToInsights()
        composeRule.onNodeWithContentDescription("insights_period_week").assertIsDisplayed()
        composeRule.onNodeWithContentDescription("insights_period_month").assertIsDisplayed()
    }

    @Test
    fun insights_switchToMonth_updatesData() {
        navigateToInsights()
        composeRule.onNodeWithContentDescription("insights_period_month").performClick()
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("80%").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun insights_showsSummaryCards() {
        navigateToInsights()
        composeRule.waitUntilNodeWithText("完成率")
        // "完成率" appears in both summary card and completion ring section
        composeRule.onAllNodesWithText("完成率").onFirst().assertIsDisplayed()
        composeRule.onNodeWithText("总积分").assertIsDisplayed()
        composeRule.onNodeWithText("连续打卡").assertIsDisplayed()
    }

    @Test
    fun insights_showsCompletionRing() {
        navigateToInsights()
        composeRule.waitUntilNodeWithText("80%")
        composeRule.onNodeWithText("80%").assertIsDisplayed()
    }

    @Test
    fun insights_showsDailyBarChart() {
        navigateToInsights()
        composeRule.waitUntilNodeWithText("每日完成情况")
        composeRule.onNodeWithText("每日完成情况").assertIsDisplayed()
    }

    @Test
    fun insights_showsTypeBreakdown() {
        navigateToInsights()
        composeRule.waitUntilNodeWithText("任务类型分布")
        composeRule.onNodeWithText("任务类型分布").assertExists()
        // Type bars are in a LazyColumn — scroll to them
        composeRule.onNodeWithText("任务类型分布").performScrollTo()
        composeRule.onNodeWithText("任务类型分布").assertIsDisplayed()
    }
}
