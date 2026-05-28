package com.kidscheck.app.testutil

import com.google.gson.Gson
import com.kidscheck.app.data.model.*

object TestData {

    private val gson = Gson()

    fun loginResponse(username: String = "爸爸", role: String = "parent", userId: Int = 1): LoginResponse =
        LoginResponse(
            accessToken = "test-jwt-token",
            tokenType = "bearer",
            user = UserInfo(id = userId, username = username, role = role)
        )

    fun loginResponseJson(username: String = "爸爸", role: String = "parent", userId: Int = 1): String =
        gson.toJson(loginResponse(username, role, userId))

    fun childList(): List<Child> = listOf(
        Child(id = 1, name = "萝卜", nickname = "萝卜", age = 8),
        Child(id = 2, name = "蚕豆", nickname = "蚕豆", age = 6)
    )

    fun childListJson(): String = gson.toJson(childList())

    fun dailyTasks(childId: Int = 1): List<DailyTask> = listOf(
        DailyTask(
            id = 1, childId = childId, date = "2026-05-27",
            title = "阅读课文", type = "reading", points = 10,
            status = "pending", completedAt = null, completedBy = null,
            isConditional = false, isAdhoc = false,
            description = "阅读第三课"
        ),
        DailyTask(
            id = 2, childId = childId, date = "2026-05-27",
            title = "写字练习", type = "written", points = 15,
            status = "pending", completedAt = null, completedBy = null,
            isConditional = false, isAdhoc = false,
            description = "写生字"
        ),
        DailyTask(
            id = 3, childId = childId, date = "2026-05-27",
            title = "额外阅读", type = "reading", points = 5,
            status = "pending", completedAt = null, completedBy = null,
            isConditional = true, isAdhoc = false
        )
    )

    fun dailyTasksJson(childId: Int = 1): String = gson.toJson(dailyTasks(childId))

    fun dailyTasksEmptyJson(): String = gson.toJson(emptyList<DailyTask>())

    fun dailyTasksWithDone(childId: Int = 1): List<DailyTask> = listOf(
        DailyTask(
            id = 1, childId = childId, date = "2026-05-27",
            title = "阅读课文", type = "reading", points = 10,
            status = "done", completedAt = "2026-05-27T08:30:00+08:00", completedBy = 1,
            completedByUsername = "爸爸", isConditional = false
        ),
        DailyTask(
            id = 2, childId = childId, date = "2026-05-27",
            title = "写字练习", type = "written", points = 15,
            status = "pending", completedAt = null, completedBy = null,
            isConditional = false
        )
    )

    fun dailyTasksWithDoneJson(childId: Int = 1): String = gson.toJson(dailyTasksWithDone(childId))

    fun dailyTaskDoneJson(taskId: Int = 1): String = gson.toJson(
        DailyTask(
            id = taskId, childId = 1, date = "2026-05-27",
            title = "阅读课文", type = "reading", points = 10,
            status = "done", completedAt = "2026-05-27T08:30:00+08:00", completedBy = 1,
            completedByUsername = "爸爸", isConditional = false
        )
    )

    fun dailyTaskPendingJson(taskId: Int = 1): String = gson.toJson(
        DailyTask(
            id = taskId, childId = 1, date = "2026-05-27",
            title = "阅读课文", type = "reading", points = 10,
            status = "pending", completedAt = null, completedBy = null,
            isConditional = false
        )
    )

    fun progressResponse(childId: Int = 1): ProgressResponse = ProgressResponse(
        childId = childId,
        date = "2026-05-27",
        totalTasks = 5,
        completedTasks = 3,
        todayPoints = 30,
        cumulativePoints = 150,
        tasks = dailyTasks(childId).map {
            if (it.id <= 2) it.copy(status = "done", completedAt = "2026-05-27T08:30:00+08:00", completedBy = 1, completedByUsername = "爸爸")
            else it
        }
    )

    fun progressResponseJson(childId: Int = 1): String = gson.toJson(progressResponse(childId))

    fun progressResponseEmptyJson(): String = gson.toJson(
        ProgressResponse(
            childId = 1, date = "2026-05-27",
            totalTasks = 0, completedTasks = 0,
            todayPoints = 0, cumulativePoints = 0,
            tasks = emptyList()
        )
    )

    fun insightsResponse(childId: Int = 1): InsightsResponse = InsightsResponse(
        childId = childId,
        period = "week",
        totalTasks = 35,
        completedTasks = 28,
        completionRate = 80f,
        totalPointsEarned = 200,
        dailyStats = (1..7).map { i ->
            DailyStatItem(date = "2026-05-${20 + i}", total = 5, completed = 4, points = 30)
        },
        completionsByType = mapOf("written" to 15, "reading" to 13),
        streak = 5
    )

    fun insightsResponseJson(childId: Int = 1): String = gson.toJson(insightsResponse(childId))

    fun templatesByWeekday(childId: Int = 1): List<TemplatesByWeekday> = listOf(
        TemplatesByWeekday(
            weekday = 1, weekdayName = "周一",
            templates = listOf(
                TaskTemplate(id = 1, childId = childId, weekday = 1, title = "阅读课文", type = "reading", description = null, points = 10, sortOrder = 0),
                TaskTemplate(id = 2, childId = childId, weekday = 1, title = "写字练习", type = "written", description = "写生字", points = 15, sortOrder = 1)
            )
        ),
        TemplatesByWeekday(
            weekday = 2, weekdayName = "周二",
            templates = listOf(
                TaskTemplate(id = 3, childId = childId, weekday = 2, title = "阅读课文", type = "reading", description = null, points = 10, sortOrder = 0)
            )
        )
    )

    fun templatesByWeekdayJson(childId: Int = 1): String = gson.toJson(templatesByWeekday(childId))

    fun conditionalTasks(childId: Int = 1): List<ConditionalTask> = listOf(
        ConditionalTask(
            id = 1, childId = childId, triggerCondition = "all_required_done",
            title = "额外阅读", type = "reading", description = null, points = 5,
            weekdays = "1,2,3,4,5"
        )
    )

    fun conditionalTasksJson(childId: Int = 1): String = gson.toJson(conditionalTasks(childId))

    fun rewards(): List<Reward> = listOf(
        Reward(id = 1, title = "冰淇淋", costPoints = 50, description = "一个冰淇淋", imageUrl = null),
        Reward(id = 2, title = "看电影", costPoints = 100, description = "看一场电影", imageUrl = null)
    )

    fun rewardsJson(): String = gson.toJson(rewards())

    fun pointBalance(childId: Int = 1, balance: Int = 100): PointBalance =
        PointBalance(childId = childId, balance = balance, transactions = emptyList())

    fun pointBalanceJson(childId: Int = 1, balance: Int = 100): String =
        gson.toJson(pointBalance(childId, balance))

    fun redemptions(): List<RewardRedemption> = listOf(
        RewardRedemption(
            id = 1, childId = 1, childName = "萝卜", rewardId = 1,
            rewardTitle = "冰淇淋", pointsSpent = 50,
            redeemedAt = "2026-05-25T10:00:00", status = "pending", photoUrl = null
        )
    )

    fun redemptionsJson(): String = gson.toJson(redemptions())

    fun redemptionsEmptyJson(): String = gson.toJson(emptyList<RewardRedemption>())

    fun emptyListJson(): String = "[]"
}
