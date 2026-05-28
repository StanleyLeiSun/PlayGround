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
class TaskListScreenTest {

    @get:Rule
    val mockRule = MockWebServerRule(preLoginUsername = "爸爸")

    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    private val dispatcher get() = mockRule.dispatcher

    private fun setupCommonMocks() {
        dispatcher.register("GET", "/api/children", TestData.childListJson())
        dispatcher.register("GET", "/api/app/version", """{"version_code":10100,"version_name":"1.1.0","release_notes":"","force_update":false}""")
    }

    private fun setupTasksAndNavigate() {
        setupCommonMocks()
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksJson())
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("📋 必做任务").fetchSemanticsNodes().isNotEmpty()
        }
    }

    private fun setupEmptyTasksAndNavigate() {
        setupCommonMocks()
        // Wait for initial task load (from pre-registered mocks)
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("📋 必做任务").fetchSemanticsNodes().isNotEmpty()
        }
        // Register empty tasks mock (overrides pre-registered due to reversed iteration)
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksEmptyJson())
        dispatcher.register("GET", "/api/progress/.*", TestData.progressResponseJson())
        // Navigate away and back to trigger a fresh load with empty data
        composeRule.onNodeWithText("进度").performClick()
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithContentDescription("progress_prev_day").fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onAllNodesWithText("今日任务").onFirst().performClick()
        composeRule.waitUntilNodeWithContentDescription("task_list_empty")
    }

    @Test
    fun taskList_showsRequiredAndConditionalSections() {
        setupTasksAndNavigate()
        composeRule.onNodeWithText("📋 必做任务").assertIsDisplayed()
        composeRule.onNodeWithText("条件任务", substring = true).assertIsDisplayed()
    }

    @Test
    fun taskList_showsTaskCards_withCorrectInfo() {
        setupTasksAndNavigate()
        composeRule.onNodeWithText("阅读课文").assertIsDisplayed()
        composeRule.onNodeWithText("写字练习").assertIsDisplayed()
        composeRule.onNodeWithText("+10分").assertIsDisplayed()
    }

    @Test
    fun taskList_emptyState_showsMessage() {
        setupEmptyTasksAndNavigate()
        composeRule.onNodeWithContentDescription("task_list_empty").assertTextContains("今天没有任务")
    }

    @Test
    fun taskList_readingTask_checkIn_confirmFlow() {
        setupTasksAndNavigate()
        composeRule.onNodeWithText("阅读课文").performClick()

        composeRule.waitUntilNodeWithText("确认完成")
        composeRule.onNodeWithText("确认完成").assertIsDisplayed()

        dispatcher.register("POST", "/api/daily-tasks/1/check-in", TestData.dailyTaskDoneJson(1))
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksWithDoneJson())
        composeRule.onNodeWithContentDescription("task_checkin_confirm").performClick()

        composeRule.waitUntil(timeoutMillis = 3000) {
            composeRule.onAllNodesWithContentDescription("task_celebration").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun taskList_writtenTask_showsPhotoOptions() {
        setupTasksAndNavigate()
        composeRule.onNodeWithText("写字练习").performClick()

        composeRule.waitUntilNodeWithText("拍照存证并完成")
        composeRule.onNodeWithText("拍照存证并完成").assertIsDisplayed()
        composeRule.onNodeWithText("从相册选择并完成").assertIsDisplayed()
    }

    @Test
    fun taskList_doneTask_showsUndoDialog() {
        setupCommonMocks()
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksWithDoneJson())
        composeRule.waitUntilNodeWithText("阅读课文")
        composeRule.onNodeWithText("阅读课文").performClick()

        composeRule.waitUntilNodeWithText("撤销完成")
        composeRule.onNodeWithText("撤销完成").assertIsDisplayed()
        composeRule.onNodeWithText("确认撤销").assertIsDisplayed()
    }

    @Test
    fun taskList_undoCheckIn_confirmsAndReloads() {
        setupCommonMocks()
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksWithDoneJson())
        composeRule.waitUntilNodeWithText("阅读课文")
        composeRule.onNodeWithText("阅读课文").performClick()

        composeRule.waitUntilNodeWithText("确认撤销")
        dispatcher.register("POST", "/api/daily-tasks/1/undo", TestData.dailyTaskPendingJson(1))
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksJson())
        composeRule.onNodeWithContentDescription("task_undo_confirm").performClick()

        // "已撤销" is a Toast — verify dialog closes and task list reloads instead
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("撤销完成").fetchSemanticsNodes().isEmpty()
        }
    }

    @Test
    fun taskList_adhocFab_opensDialog() {
        setupTasksAndNavigate()
        composeRule.onNodeWithContentDescription("task_adhoc_fab").performClick()

        composeRule.waitUntilNodeWithText("添加临时任务")
        composeRule.onNodeWithText("添加临时任务").assertIsDisplayed()
        composeRule.onNodeWithContentDescription("task_adhoc_title").assertIsDisplayed()
    }

    @Test
    fun taskList_adhocTask_create_success() {
        setupTasksAndNavigate()
        composeRule.onNodeWithContentDescription("task_adhoc_fab").performClick()

        composeRule.waitUntilNodeWithContentDescription("task_adhoc_title")
        composeRule.onNodeWithContentDescription("task_adhoc_title").performTextInput("临时任务")

        dispatcher.register("POST", "/api/daily-tasks/.*/adhoc", """{"id":99,"child_id":1,"date":"2026-05-27","title":"临时任务","type":"reading","points":5,"status":"pending","completed_at":null,"completed_by":null,"is_conditional":false,"is_adhoc":true}""")
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksJson())
        composeRule.onNodeWithText("添加").performClick()

        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("添加临时任务").fetchSemanticsNodes().isEmpty()
        }
    }

    @Test
    fun taskList_showsPhotoBadge_forWrittenTasks() {
        setupTasksAndNavigate()
        composeRule.onNodeWithText("📷 拍照").assertIsDisplayed()
    }
}
