package com.kidscheck.app.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "cached_daily_tasks")
data class CachedDailyTask(
    @PrimaryKey val id: Int,
    val childId: Int,
    val date: String,
    val title: String,
    val type: String,
    val points: Int,
    val status: String,
    val completedAt: String?,
    val completedBy: Int?,
    val isConditional: Boolean,
    val oralImageUrl: String? = null,
    val cachedAt: Long = System.currentTimeMillis()
)
