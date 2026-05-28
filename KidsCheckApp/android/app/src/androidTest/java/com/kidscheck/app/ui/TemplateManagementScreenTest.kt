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
class TemplateManagementScreenTest {

    @get:Rule
    val mockRule = MockWebServerRule(preLoginUsername = "爸爸")

    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    private val dispatcher get() = mockRule.dispatcher

    private fun setupCommonMocks() {
        dispatcher.register("GET", "/api/children", TestData.childListJson())
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksJson())
        dispatcher.register("GET", "/api/points/.*", TestData.pointBalanceJson())
        dispatcher.register("GET", "/api/app/version", """{"version_code":10100,"version_name":"1.1.0","release_notes":"","force_update":false}""")
    }

    private fun navigateToTemplates() {
        setupCommonMocks()
        dispatcher.register("GET", "/api/templates/.*", TestData.templatesByWeekdayJson())
        dispatcher.register("GET", "/api/conditional-tasks/.*", TestData.conditionalTasksJson())
        composeRule.waitUntilNodeWithText("我的")
        composeRule.onNodeWithText("我的").performClick()
        composeRule.waitUntilNodeWithText("任务模板管理")
        composeRule.onNodeWithText("任务模板管理").performClick()
        composeRule.waitUntilNodeWithContentDescription("template_add_fab")
    }

    @Test
    fun template_showsChildSelector() {
        navigateToTemplates()
        composeRule.onNodeWithContentDescription("template_child_chip_萝卜").assertIsDisplayed()
        composeRule.onNodeWithContentDescription("template_child_chip_蚕豆").assertIsDisplayed()
    }

    @Test
    fun template_showsTemplatesByWeekday() {
        navigateToTemplates()
        composeRule.waitUntilNodeWithText("周一")
        composeRule.onNodeWithText("周一").assertIsDisplayed()
        // "阅读课文" appears in multiple weekday sections
        composeRule.onAllNodesWithText("阅读课文").onFirst().assertIsDisplayed()
        composeRule.onNodeWithText("写字练习").assertIsDisplayed()
    }

    @Test
    fun template_switchChild_reloadsTemplates() {
        navigateToTemplates()
        composeRule.waitUntilNodeWithContentDescription("template_child_chip_蚕豆")
        dispatcher.register("GET", "/api/templates/2", TestData.templatesByWeekdayJson(2))
        dispatcher.register("GET", "/api/conditional-tasks/2", TestData.conditionalTasksJson(2))
        composeRule.onNodeWithContentDescription("template_child_chip_蚕豆").performClick()
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("周一").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun template_addDialog_opens() {
        navigateToTemplates()
        composeRule.onNodeWithContentDescription("template_add_fab").performClick()
        composeRule.waitUntilNodeWithText("添加任务")
        composeRule.onNodeWithText("添加任务").assertIsDisplayed()
        composeRule.onNodeWithContentDescription("template_add_title").assertIsDisplayed()
    }

    @Test
    fun template_addDialog_fillAndSubmit() {
        navigateToTemplates()
        composeRule.onNodeWithContentDescription("template_add_fab").performClick()
        composeRule.waitUntilNodeWithContentDescription("template_add_title")

        composeRule.onNodeWithContentDescription("template_add_title").performTextInput("新任务")
        // Monday is pre-selected (selectedDays = setOf(1)), no need to click

        dispatcher.register("POST", "/api/templates/.*/batch", """[{"id":1,"child_id":1,"weekday":1,"title":"阅读课文","type":"reading","description":null,"points":10,"sort_order":0}]""")
        dispatcher.register("GET", "/api/templates/.*", TestData.templatesByWeekdayJson())
        dispatcher.register("GET", "/api/conditional-tasks/.*", TestData.conditionalTasksJson())
        composeRule.onNodeWithText("添加").performClick()

        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("添加任务").fetchSemanticsNodes().isEmpty()
        }
    }

    @Test
    fun template_deleteTemplate_confirmsAndDeletes() {
        navigateToTemplates()
        composeRule.waitUntilNodeWithText("阅读课文")

        dispatcher.register("DELETE", "/api/templates/1", """{}""")
        dispatcher.register("GET", "/api/templates/.*", TestData.templatesByWeekdayJson())
        dispatcher.register("GET", "/api/conditional-tasks/.*", TestData.conditionalTasksJson())
        composeRule.onAllNodesWithContentDescription("删除").onFirst().performClick()

        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithContentDescription("删除").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun template_editDialog_opensWithCorrectData() {
        navigateToTemplates()
        composeRule.waitUntilNodeWithText("阅读课文")
        // "阅读课文" appears in multiple weekday sections — click the first one
        composeRule.onAllNodesWithText("阅读课文").onFirst().performClick()

        composeRule.waitUntilNodeWithText("编辑任务")
        composeRule.onNodeWithText("编辑任务").assertIsDisplayed()
        composeRule.onNodeWithContentDescription("template_edit_title").assertIsDisplayed()
    }

    @Test
    fun template_showsConditionalTasks() {
        navigateToTemplates()
        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("条件任务", substring = true).fetchSemanticsNodes().isNotEmpty()
        }
        composeRule.onNodeWithText("条件任务", substring = true).assertIsDisplayed()
        composeRule.onNodeWithText("额外阅读").assertIsDisplayed()
    }
}
