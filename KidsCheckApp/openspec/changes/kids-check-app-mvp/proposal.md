## Why

父母上班无法全天陪伴孩子学习，日常由爷爷奶奶看护。但爷爷奶奶不清楚每天要做哪些作业、缺少监督手段和完成记录。需要一个简单的工具让父母远程设定任务、爷爷奶奶现场打卡拍照存证、父母异步审核，形成学习管理闭环。

## What Changes

- 新建 Android 应用（Kotlin + Jetpack Compose），支持父母和爷爷奶奶两种角色
- 新建 Python FastAPI 后端，提供 RESTful API
- 实现家庭管理：创建家庭、邀请成员、管理孩子档案
- 实现周任务模板：按周一到周日设置重复任务，支持条件任务（全部完成后解锁）
- 实现每日任务自动生成（定时从模板创建当日任务实例）
- 实现打卡流程：确认完成 + 拍照存证（书面类必拍、阅读类可选）
- 实现打卡进度独立页面：时间线视图 + 照片审核
- 实现积分系统：完成任务自动发放积分、积分兑换奖励
- 实现语音输入任务管理：Android STT + 大模型意图解析

## Capabilities

### New Capabilities
- `family-management`: 家庭创建、邀请码加入、角色管理（父母/爷爷奶奶）、孩子档案 CRUD
- `task-template`: 周任务模板管理（按周几配置重复任务）、条件任务配置、语音输入创建任务
- `daily-task-generation`: 每日定时从模板自动生成任务实例、条件任务动态触发
- `check-in`: 打卡流程（确认完成 + 拍照存证）、照片上传与存储
- `progress-tracking`: 打卡进度时间线、照片审核、每日完成统计
- `points-and-rewards`: 积分自动发放、积分账户管理、奖励库管理、积分兑换与兑现确认

### Modified Capabilities

## Impact

- **新增代码**：Android 客户端（Kotlin/Compose）、Python FastAPI 后端服务
- **数据库**：PostgreSQL，新建 11 张表（family, user, child, task_template, conditional_task, daily_task, check_in_photo, point_account, point_transaction, reward, reward_redemption）
- **外部依赖**：大模型 API（通义千问/GPT，用于语音意图解析）、Android 系统 STT
- **部署**：单台轻量云服务器，需要定时任务调度（APScheduler）
- **文件存储**：照片存储（本地文件系统或 OSS）
