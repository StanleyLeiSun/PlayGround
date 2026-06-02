# 英语口语练习任务

## 概述

新增 `oral` 任务类型，支持父母上传练习图片，小孩查看图片后录音练习英语口语，录音提交后任务自动完成。家长可在进度页回听录音并决定是否撤销。

## 用户流程

1. **家长**在模板管理页创建口语任务模板，上传练习图片
2. **家长**可随时更新图片，更新前每天生成的任务沿用当前图片
3. **系统**每日生成 DailyTask 时，将模板当前图片 URL 快照到任务记录
4. **小孩**点击口语任务 → 进入独立练习页面 → 查看图片（可滑动缩放）→ 录音
5. **小孩**录音完成后试听 → 提交 → 任务自动完成，积分发放
6. **家长**在进度页查看口语任务 → 播放录音 → 不满意可 undo（保留录音，撤销完成状态）

## 数据模型

### TaskType 枚举扩展

```python
class TaskType(str, Enum):
    written = "written"
    reading = "reading"
    oral = "oral"
```

### TaskTemplate 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| oral_image_url | String, nullable | 当前口语练习图片路径，仅 oral 类型使用 |

### DailyTask 新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| oral_image_url | String, nullable | 生成时从模板快照的图片 URL |

### 新建 OralRecording 模型

```python
class OralRecording(Base):
    __tablename__ = "oral_recordings"

    id = Column(Integer, primary_key=True)
    daily_task_id = Column(Integer, ForeignKey("daily_tasks.id"), nullable=False)
    audio_url = Column(String, nullable=False)
    duration = Column(Float, nullable=False)  # 秒
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    recorded_at = Column(DateTime, default=func.now())
```

关系：DailyTask → OralRecording (one-to-many，支持重录场景保留历史)

## API 设计

### 1. 上传/更新模板口语图片

```
PUT /api/templates/{template_id}/oral-image
Content-Type: multipart/form-data
Body: image (file)
Auth: require_parent

Response 200:
{ "oral_image_url": "/photos/oral/{template_id}/{uuid}.jpg" }

Errors:
- 404: 模板不存在
- 400: 模板类型不是 oral
- 400: 文件过大（>5MB）或格式不支持
```

存储路径：`uploads/photos/oral/{template_id}/{uuid}.{ext}`

### 2. 上传录音（提交即完成任务）

```
POST /api/daily-tasks/{task_id}/recording
Content-Type: multipart/form-data
Body: audio (file), duration (float)
Auth: 任何已登录用户

Response 200:
{
  "recording": { "id", "audio_url", "duration", "recorded_by", "recorded_at" },
  "task": { ... (完成后的 DailyTask) }
}

Errors:
- 404: 任务不存在
- 400: 任务类型不是 oral
- 400: 任务已完成
- 400: duration < 30
- 400: 文件格式不是 AAC/M4A
```

行为：
1. 保存音频文件到 `uploads/recordings/{child_id}/{date}/{uuid}.m4a`
2. 创建 OralRecording 记录
3. 标记任务完成（status=done, completed_at, completed_by）
4. 发放积分
5. 触发条件任务检查

### 3. 获取任务录音

```
GET /api/daily-tasks/{task_id}/recordings
Auth: 任何已登录用户

Response 200:
[{ "id", "audio_url", "duration", "recorded_by", "recorded_at" }]
```

返回该任务关联的所有录音（含重录历史），按时间倒序。

### 4. 任务完成/撤销

- 完成：由录音上传接口自动触发，无需单独调用 check-in
- 撤销：复用现有 `POST /api/daily-tasks/{task_id}/undo`
  - 行为：撤销完成状态、扣回积分
  - **保留录音记录和文件**（孩子已练过，录音本身有价值）

## 任务生成逻辑变更

`daily_task_service.generate_daily_tasks()` 生成口语任务时：
- 从 TaskTemplate 复制 `oral_image_url` 到 DailyTask 的同名字段
- 若模板 `oral_image_url` 为空（家长还未上传图片），仍生成任务但客户端显示提示

## Android 客户端

### 任务列表页变更

- TaskCard 对 `type="oral"` 显示 🎤 标识
- 点击口语任务跳转独立练习页面（非弹窗）

### 口语练习页面 (OralPracticeScreen)

**状态机：** Ready → Recording → Recorded → Submitting → Done

**Ready 状态：**
- 顶部返回按钮 + 标题"英语口语练习"
- 任务标题/描述卡片
- 图片区域占主体，支持手势滑动和双指缩放（使用 Compose 的 `Modifier.pointerInput` + `transformable`）
- 底部录音按钮（红色圆形），提示"点击开始录音 · 30秒~5分钟"

**Recording 状态：**
- 顶部显示"正在录音"+ 计时器
- 图片区域不变，仍可滑动缩放
- 返回按钮禁用
- 底部停止按钮（红色方块图标）+ 声波动画
- 不足 30 秒时显示警告提示
- 5 分钟自动停止

**Recorded 状态：**
- 图片缩小显示
- 音频播放器（播放/暂停 + 进度条 + 时长）
- "重录"和"提交完成"按钮

**Submitting 状态：**
- 提交按钮显示加载状态
- 禁止交互

**Done 状态：**
- 显示完成动画后自动返回任务列表

### 录音实现

使用 Android `MediaRecorder` API：
- 输出格式：`OutputFormat.MPEG_4`
- 编码器：`AudioEncoder.AAC`
- 输出文件：应用缓存目录临时文件
- 播放使用 `MediaPlayer`

### 进度页变更

口语任务的详情区域显示音频播放器控件，家长可回听录音。

### 模板管理页变更

- 创建/编辑模板时，类型选择新增"口语"选项
- 选择"口语"后显示图片上传区域（拍照/相册）
- 已有图片时显示缩略图 + "更换图片"按钮

## 文件存储

| 类型 | 路径 | 说明 |
|------|------|------|
| 模板图片 | `uploads/photos/oral/{template_id}/{uuid}.{ext}` | 家长上传的练习图 |
| 录音文件 | `uploads/recordings/{child_id}/{date}/{uuid}.m4a` | 小孩提交的录音 |

两类文件均通过 FastAPI 静态挂载提供访问：
- 图片：现有 `/photos` 挂载覆盖
- 录音：新增 `/recordings` 静态挂载指向 `uploads/recordings/`

## 测试方案

### 后端测试

新建 `tests/test_oral_task.py`，覆盖以下场景：

**模板图片管理：**
- 上传图片到 oral 类型模板 → 成功，返回 URL
- 上传图片到非 oral 类型模板 → 400 错误
- 替换已有图片 → 成功，URL 更新
- 超大文件上传 → 400 错误

**任务生成：**
- 有图片的口语模板 → DailyTask 的 oral_image_url 正确快照
- 无图片的口语模板 → DailyTask 仍正常生成，oral_image_url 为 null
- 更新模板图片后重新生成 → 新任务用新图片，旧任务保留旧图片

**录音上传与任务完成：**
- 上传录音（duration >= 30）→ 成功，任务自动标记完成，积分发放
- 上传录音（duration < 30）→ 400 错误
- 对非 oral 类型任务上传录音 → 400 错误
- 对已完成任务上传录音 → 400 错误
- 录音上传后触发条件任务检查

**录音获取：**
- 获取任务录音列表 → 返回按时间倒序
- 无录音时 → 返回空列表

**Undo 行为：**
- 撤销口语任务 → 状态恢复，积分扣回，录音记录保留

测试使用 `committed_db` fixture（需要数据对 API 可见），模拟音频文件用 `b'\x00' * 1024` 字节。

### Android 客户端测试

**单元测试（test/）：**
- OralRecording 数据模型序列化/反序列化
- 录音时长校验逻辑（< 30 秒不允许提交）
- 计时器格式化函数

**UI 测试（androidTest/）：**

新建 `OralPracticeScreenTest.kt`：
- Mock 口语任务数据 → 任务列表正确显示 🎤 标识
- 点击口语任务 → 导航到练习页面
- 练习页面图片正确加载
- 录音按钮点击 → 进入录音状态，计时器开始
- 停止录音 → 进入试听状态，播放器显示
- 点击提交 → API 调用成功，返回任务列表

使用 MockWebServer 模拟后端响应，遵循现有 `MockApiDispatcher` 模式注册新端点。

## 升级部署方案

### 数据库迁移

创建新的 Alembic 迁移：

```bash
cd backend
./.venv/bin/python -m alembic revision --autogenerate -m "add_oral_task_type"
```

迁移内容：
1. `task_templates` 表新增 `oral_image_url` 列（nullable，无默认值）
2. `daily_tasks` 表新增 `oral_image_url` 列（nullable，无默认值）
3. 新建 `oral_recordings` 表

所有变更均为**加法操作**（新增列、新增表），不修改/删除现有数据，无破坏性风险。

downgrade 函数：
1. 删除 `oral_recordings` 表
2. 删除 `daily_tasks.oral_image_url` 列
3. 删除 `task_templates.oral_image_url` 列

### 部署步骤

遵循现有 SOP（`docs/sop/deploy-backend-prod.md`）：

**1. 部署前备份（服务器端）：**
```bash
# 备份数据库
cp /opt/kidscheck/kidscheck.db /opt/kidscheck/backups/kidscheck_$(date +%Y%m%d_%H%M%S).db

# 备份上传文件目录
tar czf /opt/kidscheck/backups/uploads_$(date +%Y%m%d_%H%M%S).tar.gz /opt/kidscheck/uploads/
```

**2. 部署代码：**
```bash
# 本地打包（排除 db、uploads、.env）
tar czf kidscheck-backend.tar.gz --exclude='*.db' --exclude='uploads' --exclude='.env*' backend/

# 上传到服务器
scp kidscheck-backend.tar.gz root@47.94.167.238:/opt/kidscheck/

# SSH 到服务器执行
ssh root@47.94.167.238
cd /opt/kidscheck
tar xzf kidscheck-backend.tar.gz --strip-components=1
```

**3. 更新依赖 + 运行迁移：**
```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m alembic upgrade head
```

**4. 创建录音存储目录：**
```bash
mkdir -p /opt/kidscheck/uploads/recordings
```

**5. 更新 Nginx 配置（新增录音静态文件）：**
```nginx
location /recordings/ {
    alias /opt/kidscheck/uploads/recordings/;
}
```

**6. 重启服务：**
```bash
nginx -t && systemctl reload nginx
systemctl restart kidscheck
```

**7. 验证：**
```bash
# 健康检查
curl http://localhost:8000/docs

# 验证新端点存在
curl -s http://localhost:8000/openapi.json | python -m json.tool | grep oral
```

### 回滚方案

如果部署出现问题：

```bash
# 恢复数据库
cp /opt/kidscheck/backups/kidscheck_YYYYMMDD_HHMMSS.db /opt/kidscheck/kidscheck.db

# 或者仅回滚迁移（保留代码更新）
python -m alembic downgrade -1

# 重启服务
systemctl restart kidscheck
```

### Android 客户端发布

1. 使用 `scripts/release-apk.sh patch` 进行版本号递增
2. 构建生产包，自动生成 `version.json`
3. 客户端自动更新机制会检测新版本并提示用户升级
4. 口语功能需要新客户端，旧客户端遇到 `type="oral"` 的任务会显示为普通任务（降级为 reading 展示），不影响使用

### 兼容性说明

- 后端先部署：新增的 `oral_image_url` 字段为 nullable，旧客户端不受影响
- 客户端后发布：新 API 端点只在新客户端使用，不影响旧版本
- TaskType 枚举扩展：旧客户端解析未知类型时忽略或降级显示
- 无需停机维护，支持滚动升级
