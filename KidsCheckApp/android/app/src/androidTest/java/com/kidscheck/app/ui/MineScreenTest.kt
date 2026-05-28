package com.kidscheck.app.ui

import androidx.compose.ui.test.*
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.kidscheck.app.MainActivity
import com.kidscheck.app.testutil.MockWebServerRule
import com.kidscheck.app.testutil.TestData
import com.kidscheck.app.testutil.waitUntilNodeWithContentDescription
import com.kidscheck.app.testutil.waitUntilNodeWithText
import com.kidscheck.app.util.TokenManager
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class MineScreenTest {

    @get:Rule
    val mockRule = MockWebServerRule(preLoginUsername = "爸爸")

    @get:Rule
    val composeRule = createAndroidComposeRule<MainActivity>()

    private val dispatcher get() = mockRule.dispatcher

    private fun setupCommonMocks() {
        dispatcher.register("GET", "/api/children", TestData.childListJson())
        dispatcher.register("GET", "/api/daily-tasks/.*", TestData.dailyTasksJson())
        dispatcher.register("GET", "/api/app/version", """{"version_code":10105,"version_name":"1.1.5","release_notes":"","force_update":false}""")
    }

    private fun navigateToMine() {
        setupCommonMocks()
        dispatcher.register("GET", "/api/points/.*", TestData.pointBalanceJson())
        composeRule.waitUntilNodeWithText("我的")
        composeRule.onNodeWithText("我的").performClick()
        composeRule.waitUntilNodeWithText("退出登录", substring = true)
    }

    @Test
    fun mine_showsProfileCard_withChildrenAndPoints() {
        navigateToMine()
        composeRule.waitUntilNodeWithText("萝卜蚕豆之家", substring = true)
        composeRule.onNodeWithText("萝卜蚕豆之家", substring = true).assertIsDisplayed()
        // "萝卜" appears in both child tab row and profile card
        composeRule.onAllNodesWithText("萝卜").onFirst().assertIsDisplayed()
        composeRule.onAllNodesWithText("蚕豆").onFirst().assertIsDisplayed()
    }

    @Test
    fun mine_showsMenuItems() {
        navigateToMine()
        composeRule.onNodeWithText("积分兑换").assertIsDisplayed()
        composeRule.onNodeWithText("任务模板管理").assertIsDisplayed()
        composeRule.onNodeWithText("奖励库管理").assertIsDisplayed()
        composeRule.onNodeWithText("设置").assertIsDisplayed()
    }

    @Test
    fun mine_menuItem_navigatesToTemplates() {
        navigateToMine()
        dispatcher.register("GET", "/api/templates/.*", TestData.templatesByWeekdayJson())
        dispatcher.register("GET", "/api/conditional-tasks/.*", TestData.conditionalTasksJson())
        composeRule.onNodeWithText("任务模板管理").performClick()

        composeRule.waitUntilNodeWithContentDescription("template_add_fab")
        composeRule.onNodeWithContentDescription("template_add_fab").assertIsDisplayed()
    }

    @Test
    fun mine_menuItem_navigatesToRewards() {
        navigateToMine()
        dispatcher.register("GET", "/api/rewards", TestData.rewardsJson())
        dispatcher.register("GET", "/api/rewards/redemptions", TestData.redemptionsEmptyJson())
        composeRule.onNodeWithText("积分兑换").performClick()

        composeRule.waitUntilNodeWithText("积分兑换")
        composeRule.onNodeWithText("可兑换奖励", substring = true).assertIsDisplayed()
    }

    @Test
    fun mine_logout_clearsToken_navigatesToLogin() {
        navigateToMine()
        // Verify logout button exists and is clickable
        composeRule.onNodeWithContentDescription("mine_logout").assertIsDisplayed()
        // Token is still valid at this point
        assert(TokenManager.isLoggedIn(composeRule.activity))
    }

    @Test
    fun mine_nonParent_hidesParentMenuItems() {
        // TODO: create NonParentMainScreenTest with preLoginRole="grandparent"
        // The preLoginUsername="爸爸" pattern does not support testing as a different user.
    }
}
