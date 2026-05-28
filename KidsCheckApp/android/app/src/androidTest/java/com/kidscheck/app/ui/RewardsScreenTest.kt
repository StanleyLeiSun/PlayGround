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
class RewardsScreenTest {

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

    private fun navigateToRewards() {
        setupCommonMocks()
        dispatcher.register("GET", "/api/rewards", TestData.rewardsJson())
        dispatcher.register("GET", "/api/rewards/redemptions", TestData.redemptionsEmptyJson())
        composeRule.waitUntilNodeWithText("我的")
        composeRule.onNodeWithText("我的").performClick()
        composeRule.waitUntilNodeWithText("奖励库管理")
        composeRule.onNodeWithText("奖励库管理").performClick()
        composeRule.waitUntilNodeWithContentDescription("reward_add_fab")
    }

    @Test
    fun rewards_showsRewardList() {
        navigateToRewards()
        composeRule.waitUntilNodeWithText("冰淇淋")
        composeRule.onNodeWithText("冰淇淋").assertIsDisplayed()
        composeRule.onNodeWithText("看电影").assertIsDisplayed()
        composeRule.onNodeWithText("需要 50 积分").assertIsDisplayed()
    }

    @Test
    fun rewards_showsChildPoints() {
        navigateToRewards()
        composeRule.waitUntilNodeWithText("萝卜", substring = true)
        composeRule.onNodeWithText("萝卜", substring = true).assertIsDisplayed()
    }

    @Test
    fun rewards_addDialog_opens() {
        navigateToRewards()
        composeRule.onNodeWithContentDescription("reward_add_fab").performClick()
        composeRule.waitUntilNodeWithText("添加奖励")
        composeRule.onNodeWithText("添加奖励").assertIsDisplayed()
        composeRule.onNodeWithContentDescription("reward_add_title").assertIsDisplayed()
    }

    @Test
    fun rewards_addDialog_fillAndSubmit() {
        navigateToRewards()
        composeRule.onNodeWithContentDescription("reward_add_fab").performClick()
        composeRule.waitUntilNodeWithContentDescription("reward_add_title")

        composeRule.onNodeWithContentDescription("reward_add_title").performTextInput("新奖励")
        composeRule.onNodeWithContentDescription("reward_add_cost").performTextInput("30")

        dispatcher.register("POST", "/api/rewards", """{"id":3,"title":"新奖励","cost_points":30,"description":null,"image_url":null}""")
        dispatcher.register("GET", "/api/rewards", TestData.rewardsJson())
        dispatcher.register("GET", "/api/rewards/redemptions", TestData.redemptionsEmptyJson())
        composeRule.onNodeWithText("添加").performClick()

        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithText("添加奖励").fetchSemanticsNodes().isEmpty()
        }
    }

    @Test
    fun rewards_redeemSheet_opens() {
        navigateToRewards()
        composeRule.waitUntilNodeWithText("兑换")
        composeRule.onAllNodesWithText("兑换").onFirst().performClick()

        composeRule.waitUntilNodeWithText("确认兑换")
        composeRule.onNodeWithText("确认兑换").assertIsDisplayed()
    }

    @Test
    fun rewards_redeemSheet_confirmsRedeem() {
        navigateToRewards()
        composeRule.waitUntilNodeWithText("兑换")
        composeRule.onAllNodesWithText("兑换").onFirst().performClick()

        composeRule.waitUntilNodeWithContentDescription("reward_redeem_confirm")
        dispatcher.register("POST", "/api/rewards/.*/redeem", """{"id":1,"child_id":1,"child_name":"萝卜","reward_id":1,"reward_title":"冰淇淋","points_spent":50,"redeemed_at":"2026-05-27T10:00:00","status":"pending","photo_url":null}""")
        dispatcher.register("GET", "/api/rewards", TestData.rewardsJson())
        dispatcher.register("GET", "/api/rewards/redemptions", TestData.redemptionsJson())
        composeRule.onNodeWithContentDescription("reward_redeem_confirm").performClick()
    }

    @Test
    fun rewards_deleteReward() {
        navigateToRewards()
        composeRule.waitUntilNodeWithText("冰淇淋")

        dispatcher.register("DELETE", "/api/rewards/1", """{}""")
        dispatcher.register("GET", "/api/rewards", TestData.rewardsJson())
        dispatcher.register("GET", "/api/rewards/redemptions", TestData.redemptionsEmptyJson())
        composeRule.onAllNodesWithContentDescription("删除").onFirst().performClick()

        composeRule.waitUntil(timeoutMillis = 5000) {
            composeRule.onAllNodesWithContentDescription("删除").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @Test
    fun rewards_showsRedemptionHistory() {
        setupCommonMocks()
        dispatcher.register("GET", "/api/rewards", TestData.rewardsJson())
        dispatcher.register("GET", "/api/rewards/redemptions", TestData.redemptionsJson())
        composeRule.waitUntilNodeWithText("我的")
        composeRule.onNodeWithText("我的").performClick()
        composeRule.waitUntilNodeWithText("奖励库管理")
        composeRule.onNodeWithText("奖励库管理").performClick()
        composeRule.waitUntilNodeWithContentDescription("reward_add_fab")

        // "📋 兑换记录" has emoji prefix
        composeRule.waitUntilNodeWithText("兑换记录", substring = true)
        composeRule.onNodeWithText("兑换记录", substring = true).assertIsDisplayed()
        composeRule.onNodeWithText("-50分").assertIsDisplayed()
    }
}
