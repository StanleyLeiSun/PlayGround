package com.kidscheck.app.data.model

import com.google.gson.annotations.SerializedName

data class LoginRequest(
    val username: String,
    val password: String
)

data class LoginResponse(
    @SerializedName("access_token") val accessToken: String,
    @SerializedName("token_type") val tokenType: String,
    val user: UserInfo
)

data class UserInfo(
    val id: Int,
    val username: String,
    val role: String
)

data class Child(
    val id: Int,
    val name: String,
    val nickname: String,
    val age: Int
)

data class TaskTemplate(
    val id: Int,
    @SerializedName("child_id") val childId: Int,
    val weekday: Int,
    val title: String,
    val type: String,
    val description: String?,
    val points: Int,
    @SerializedName("sort_order") val sortOrder: Int
)

data class TemplatesByWeekday(
    val weekday: Int,
    @SerializedName("weekday_name") val weekdayName: String,
    val templates: List<TaskTemplate>
)

data class ConditionalTask(
    val id: Int,
    @SerializedName("child_id") val childId: Int,
    @SerializedName("trigger_condition") val triggerCondition: String,
    val title: String,
    val type: String,
    val description: String?,
    val points: Int,
    val weekdays: String? = null
)

data class DailyTask(
    val id: Int,
    @SerializedName("child_id") val childId: Int,
    val date: String,
    val title: String,
    val type: String,
    val points: Int,
    val status: String,
    @SerializedName("completed_at") val completedAt: String?,
    @SerializedName("completed_by") val completedBy: Int?,
    @SerializedName("completed_by_username") val completedByUsername: String? = null,
    @SerializedName("is_conditional") val isConditional: Boolean,
    @SerializedName("is_adhoc") val isAdhoc: Boolean = false,
    val description: String? = null,
    val photos: List<CheckInPhoto> = emptyList()
)

data class AdhocTaskCreate(
    val title: String,
    val type: String = "reading",
    val description: String? = null,
    val points: Int = 5
)

data class CheckInPhoto(
    val id: Int,
    @SerializedName("photo_url") val photoUrl: String,
    @SerializedName("uploaded_by") val uploadedBy: Int,
    @SerializedName("uploaded_at") val uploadedAt: String,
    val reviewed: Boolean,
    @SerializedName("review_note") val reviewNote: String?
)

data class ProgressResponse(
    @SerializedName("child_id") val childId: Int,
    val date: String,
    @SerializedName("total_tasks") val totalTasks: Int,
    @SerializedName("completed_tasks") val completedTasks: Int,
    @SerializedName("today_points") val todayPoints: Int,
    @SerializedName("cumulative_points") val cumulativePoints: Int,
    val tasks: List<DailyTask>
)

data class Reward(
    val id: Int,
    val title: String,
    @SerializedName("cost_points") val costPoints: Int,
    val description: String?,
    @SerializedName("image_url") val imageUrl: String?
)

data class VoiceParsedIntent(
    val action: String,
    val child: String?,
    val weekday: Int?,
    val title: String?,
    val type: String?,
    val points: Int?,
    @SerializedName("is_conditional") val isConditional: Boolean
)

data class PointBalance(
    @SerializedName("child_id") val childId: Int,
    val balance: Int,
    val transactions: List<PointTransaction>
)

data class PointTransaction(
    val id: Int,
    @SerializedName("child_id") val childId: Int,
    val amount: Int,
    val reason: String,
    @SerializedName("related_task_id") val relatedTaskId: Int?,
    @SerializedName("created_at") val createdAt: String
)

data class TaskTemplateCreate(
    val weekday: Int,
    val title: String,
    val type: String,
    val description: String? = null,
    val points: Int = 5,
    @SerializedName("sort_order") val sortOrder: Int = 0
)

data class TaskTemplateBatchCreate(
    val weekdays: List<Int>,
    val title: String,
    val type: String,
    val description: String? = null,
    val points: Int = 5,
    @SerializedName("sort_order") val sortOrder: Int = 0
)

data class ConditionalTaskCreate(
    val title: String,
    val type: String,
    val description: String? = null,
    val points: Int = 5,
    val weekdays: String? = null
)

data class ConditionalTaskUpdate(
    val title: String? = null,
    val type: String? = null,
    val description: String? = null,
    val points: Int? = null,
    val weekdays: String? = null
)

data class RewardCreate(
    val title: String,
    @SerializedName("cost_points") val costPoints: Int,
    val description: String? = null,
    @SerializedName("image_url") val imageUrl: String? = null
)

data class RewardRedemption(
    val id: Int,
    @SerializedName("child_id") val childId: Int,
    @SerializedName("child_name") val childName: String?,
    @SerializedName("reward_id") val rewardId: Int,
    @SerializedName("reward_title") val rewardTitle: String?,
    @SerializedName("points_spent") val pointsSpent: Int,
    @SerializedName("redeemed_at") val redeemedAt: String,
    val status: String,
    @SerializedName("photo_url") val photoUrl: String?
)

data class VoiceRequest(val text: String)

data class DailyStatItem(
    val date: String,
    val total: Int,
    val completed: Int,
    val points: Int
)

data class InsightsResponse(
    @SerializedName("child_id") val childId: Int,
    val period: String,
    @SerializedName("total_tasks") val totalTasks: Int,
    @SerializedName("completed_tasks") val completedTasks: Int,
    @SerializedName("completion_rate") val completionRate: Float,
    @SerializedName("total_points_earned") val totalPointsEarned: Int,
    @SerializedName("daily_stats") val dailyStats: List<DailyStatItem>,
    @SerializedName("completions_by_type") val completionsByType: Map<String, Int>,
    val streak: Int
)
