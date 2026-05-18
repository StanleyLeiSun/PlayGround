package com.kidscheck.app.data.local

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface DailyTaskDao {
    @Query("SELECT * FROM cached_daily_tasks WHERE childId = :childId AND date = :date ORDER BY isConditional ASC, completedAt DESC")
    suspend fun getTasks(childId: Int, date: String): List<CachedDailyTask>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(tasks: List<CachedDailyTask>)

    @Query("DELETE FROM cached_daily_tasks WHERE childId = :childId AND date = :date")
    suspend fun clearFor(childId: Int, date: String)

    @Query("DELETE FROM cached_daily_tasks WHERE cachedAt < :threshold")
    suspend fun clearOlderThan(threshold: Long)
}
