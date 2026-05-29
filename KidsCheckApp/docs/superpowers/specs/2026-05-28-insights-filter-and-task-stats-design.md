# 洞察页面过滤标签 & 任务明细改进设计

## Overview

改进洞察（DataInsights）页面的两个方面：
1. 时间过滤标签从"近7天/近30天"改为"本周/上一周/本月"，按自然周月计算
2. "任务类型分布"改为按任务名称聚合的完成明细，显示每个任务的完成天数和完成比例

## 过滤标签

### 三个选项

| 选项 | period 值 | 日期范围 |
|---|---|---|
| 本周 | `week` | 本周一 → 今天 |
| 上一周 | `last_week` | 上周一 → 上周日 |
| 本月 | `month` | 本月1号 → 今天 |

周起始日：周一（ISO 8601）。

### Backend 变更

`app/routers/insights.py` — `start_date` 计算逻辑：

```python
if period == "week":
    start_date = today - timedelta(days=today.weekday())
    end_date = today
elif period == "last_week":
    start_date = today - timedelta(days=today.weekday() + 7)
    end_date = start_date + timedelta(days=6)
else:  # month
    start_date = today.replace(day=1)
    end_date = today
```

`period` 参数 regex 从 `^(week|month)$` 改为 `^(week|last_week|month)$`。

### Android 变更

`DataInsightsScreen.kt` — FilterChip 标签更新，新增"上一周"选项：

```kotlin
FilterChip(selected = period == "week", onClick = { period = "week" }, label = { Text("本周") })
FilterChip(selected = period == "last_week", onClick = { period = "last_week" }, label = { Text("上一周") })
FilterChip(selected = period == "month", onClick = { period = "month" }, label = { Text("本月") })
```

## 任务完成明细

### 替换"任务类型分布"

移除 `completions_by_type: dict[str, int]`，新增 `task_stats: list[TaskStatItem]`。

### 新增 Schema

```python
class TaskStatItem(BaseModel):
    title: str       # 任务名称
    completed: int   # 完成天数
    total: int       # 需完成天数（该任务在周期内出现的天数）
    ratio: float     # completed / total
```

`InsightsResponse` 中 `completions_by_type` → `task_stats: list[TaskStatItem]`。

### Backend 查询

按 `DailyTask.title` 分组：

```sql
SELECT title, COUNT(*) as total,
       SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) as completed
FROM daily_task
WHERE child_id=? AND date BETWEEN ? AND ?
GROUP BY title
```

按 `ratio` 降序排列。

### Android UI

"任务完成明细"替代"任务类型分布"，每项显示：
- 左侧：任务名称
- 右侧：`X/Y天` + 进度条

## 影响文件

| 文件 | 变更 |
|---|---|
| `backend/app/routers/insights.py` | 日期计算 + task_stats 查询 |
| `backend/app/schemas/schemas.py` | 新增 TaskStatItem，修改 InsightsResponse |
| `backend/tests/test_insights.py` | 新增 last_week 测试，更新 task_stats 断言 |
| `android/.../DataInsightsScreen.kt` | 标签 + task_stats UI |
| `android/.../data/model/Models.kt` | 新增 TaskStatItem data class |
| `android/.../data/api/ApiService.kt` | 无需改动（响应自动反序列化） |

## Out of Scope

- 自定义日期范围选择
- 按周/月对比图表
- 微信小程序端同步改动
