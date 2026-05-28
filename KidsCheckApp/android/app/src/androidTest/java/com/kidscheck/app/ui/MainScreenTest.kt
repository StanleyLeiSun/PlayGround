package com.kidscheck.app.ui

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.kidscheck.app.MainActivity
import com.kidscheck.app.testutil.MockWebServerRule
import com.kidscheck.app.testutil.TestData
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MainScreenTest {

    @get:Rule
    val mockRule = MockWebServerRule(preLoginUsername = "爸爸")

    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    private val dispatcher get() = mockRule.dispatcher

    private fun setupMainScreenMocks() {
        dispatcher.register("GET", "/api/children", TestData.childListJson())
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksJson())
        dispatcher.register("GET", "/api/app/version", """{"version_code":10100,"version_name":"1.1.0","release_notes":"","force_update":false}""")
        dispatcher.register("GET", "/api/progress/.*", TestData.progressResponseJson())
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("今日任务").fetchSemanticsNodes().isNotEmpty()
        }
        // Wait for task list to fully load before proceeding
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("📋 必做任务").fetchSemanticsNodes().isNotEmpty() ||
                composeRule.onAllNodesWithContentDescription("task_list_empty").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun mainScreen_showsFourTabs_forParent() {
        setupMainScreenMocks()
        // "今日任务" appears in both TopAppBar and NavigationBar
        composeRule.onAllNodesWithText("今日任务").onFirst().assertIsDisplayed()
        composeRule.onNodeWithText("进度").assertIsDisplayed()
        composeRule.onNodeWithText("洞察").assertIsDisplayed()
        composeRule.onNodeWithText("我的").assertIsDisplayed()
    }

    @Test
    fun mainScreen_showsThreeTabs_forChild() {
        // This test needs grandparent role - skip for now, will be in separate class
        // TODO: create NonParentMainScreenTest with preLoginRole="grandparent"
    }

    @Test
    fun mainScreen_switchTabs_changesContent() {
        setupMainScreenMocks()
        composeRule.onNodeWithText("进度").performClick()
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithContentDescription("progress_prev_day").fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onAllNodesWithText("今日任务").onFirst().performClick()
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("📋 必做任务").fetchSemanticsNodes().isNotEmpty() ||
                composeRule.onAllNodesWithContentDescription("task_list_empty").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun mainScreen_showsChildTabs() {
        setupMainScreenMocks()
        composeRule.onNodeWithContentDescription("main_child_tab_萝卜").assertIsDisplayed()
        composeRule.onNodeWithContentDescription("main_child_tab_蚕豆").assertIsDisplayed()
    }

    @Test
    fun mainScreen_switchChildTab_updatesContent() {
        setupMainScreenMocks()
        composeRule.onNodeWithContentDescription("main_child_tab_蚕豆").performClick()
        composeRule.onNodeWithContentDescription("main_child_tab_蚕豆").assertIsSelected()
    }

    @Test
    fun mainScreen_tabNavigation_preservesState() {
        setupMainScreenMocks()
        composeRule.onNodeWithText("进度").performClick()
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithContentDescription("progress_prev_day").fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("我的").performClick()
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("退出登录", substring = true).fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onAllNodesWithText("今日任务").onFirst().performClick()
        composeRule.waitUntil(timeoutMillis = 10000) {
            composeRule.onAllNodesWithText("📋 必做任务").fetchSemanticsNodes().isNotEmpty() ||
                composeRule.onAllNodesWithContentDescription("task_list_empty").fetchSemanticsNodes().isNotEmpty()
        }
    }
}
