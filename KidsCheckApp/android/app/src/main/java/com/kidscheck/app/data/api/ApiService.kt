package com.kidscheck.app.data.api

import com.kidscheck.app.data.model.*
import okhttp3.MultipartBody
import retrofit2.Response
import retrofit2.http.*

interface ApiService {

    @POST("/api/auth/login")
    suspend fun login(@Body request: LoginRequest): Response<LoginResponse>

    @GET("/api/auth/me")
    suspend fun getMe(): Response<UserInfo>

    @GET("/api/children")
    suspend fun getChildren(): Response<List<Child>>

    @GET("/api/templates/{childId}")
    suspend fun getTemplates(@Path("childId") childId: Int): Response<List<TemplatesByWeekday>>

    @POST("/api/templates/{childId}")
    suspend fun createTemplate(
        @Path("childId") childId: Int,
        @Body data: TaskTemplateCreate
    ): Response<TaskTemplate>

    @POST("/api/templates/{childId}/batch")
    suspend fun createTemplateBatch(
        @Path("childId") childId: Int,
        @Body data: TaskTemplateBatchCreate
    ): Response<List<TaskTemplate>>

    @PUT("/api/templates/{id}")
    suspend fun updateTemplate(
        @Path("id") id: Int,
        @Body data: Map<String, Any>
    ): Response<TaskTemplate>

    @DELETE("/api/templates/{id}")
    suspend fun deleteTemplate(@Path("id") id: Int): Response<Unit>

    @GET("/api/conditional-tasks/{childId}")
    suspend fun getConditionalTasks(@Path("childId") childId: Int): Response<List<ConditionalTask>>

    @POST("/api/conditional-tasks/{childId}")
    suspend fun createConditionalTask(
        @Path("childId") childId: Int,
        @Body data: ConditionalTaskCreate
    ): Response<ConditionalTask>

    @DELETE("/api/conditional-tasks/{id}")
    suspend fun deleteConditionalTask(@Path("id") id: Int): Response<Unit>

    @POST("/api/templates/voice")
    suspend fun voiceInput(@Body data: VoiceRequest): Response<VoiceParsedIntent>

    @POST("/api/daily-tasks/{childId}/adhoc")
    suspend fun createAdhocTask(
        @Path("childId") childId: Int,
        @Body data: AdhocTaskCreate
    ): Response<DailyTask>

    @GET("/api/daily-tasks/{childId}/{date}")
    suspend fun getDailyTasks(
        @Path("childId") childId: Int,
        @Path("date") date: String
    ): Response<List<DailyTask>>

    @POST("/api/daily-tasks/{id}/check-in")
    suspend fun checkIn(
        @Path("id") taskId: Int
    ): Response<DailyTask>

    @Multipart
    @POST("/api/daily-tasks/{id}/check-in")
    suspend fun checkInWithPhoto(
        @Path("id") taskId: Int,
        @Part photo: MultipartBody.Part
    ): Response<DailyTask>

    @GET("/api/progress/{childId}/{date}")
    suspend fun getProgress(
        @Path("childId") childId: Int,
        @Path("date") date: String
    ): Response<ProgressResponse>

    @GET("/api/insights/{childId}")
    suspend fun getInsights(
        @Path("childId") childId: Int,
        @Query("period") period: String
    ): Response<InsightsResponse>

    @GET("/api/points/{childId}")
    suspend fun getPoints(@Path("childId") childId: Int): Response<PointBalance>

    @GET("/api/rewards")
    suspend fun getRewards(): Response<List<Reward>>

    @POST("/api/rewards")
    suspend fun createReward(@Body data: RewardCreate): Response<Reward>

    @DELETE("/api/rewards/{id}")
    suspend fun deleteReward(@Path("id") id: Int): Response<Unit>

    @POST("/api/rewards/{rewardId}/redeem")
    suspend fun redeemReward(
        @Path("rewardId") rewardId: Int,
        @Query("child_id") childId: Int
    ): Response<Unit>

    @PUT("/api/rewards/redemptions/{id}/fulfill")
    suspend fun fulfillRedemption(@Path("id") id: Int): Response<Unit>

    @PUT("/api/progress/{childId}/photo/{photoId}/review")
    suspend fun reviewPhoto(
        @Path("childId") childId: Int,
        @Path("photoId") photoId: Int,
        @Body data: Map<String, Any>
    ): Response<Unit>
}
