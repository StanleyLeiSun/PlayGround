package com.kidscheck.app.data.model

import com.google.gson.Gson
import com.google.gson.GsonBuilder
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class ModelsTest {

    private lateinit var gson: Gson

    @Before
    fun setup() {
        gson = GsonBuilder().create()
    }

    // LoginRequest Tests
    @Test
    fun `loginRequest serialization`() {
        val request = LoginRequest("baba", "123456")
        val json = gson.toJson(request)
        assertTrue(json.contains("\"username\":\"baba\""))
        assertTrue(json.contains("\"password\":\"123456\""))
    }

    @Test
    fun `loginRequest deserialization`() {
        val json = """{"username":"mama","password":"abc123"}"""
        val request = gson.fromJson(json, LoginRequest::class.java)
        assertEquals("mama", request.username)
        assertEquals("abc123", request.password)
    }

    // LoginResponse Tests
    @Test
    fun `loginResponse deserialization withSerializedName`() {
        val json = """{
            "access_token": "token123",
            "token_type": "bearer",
            "user": {"id": 1, "username": "baba", "role": "parent"}
        }"""
        val response = gson.fromJson(json, LoginResponse::class.java)
        assertEquals("token123", response.accessToken)
        assertEquals("bearer", response.tokenType)
        assertEquals(1, response.user.id)
        assertEquals("baba", response.user.username)
        assertEquals("parent", response.user.role)
    }

    // UserInfo Tests
    @Test
    fun `userInfo creation`() {
        val user = UserInfo(1, "baba", "parent")
        assertEquals(1, user.id)
        assertEquals("baba", user.username)
        assertEquals("parent", user.role)
    }

    // Child Tests
    @Test
    fun `child deserialization`() {
        val json = """{"id":1,"name":"萝卜","nickname":"萝卜","age":8}"""
        val child = gson.fromJson(json, Child::class.java)
        assertEquals(1, child.id)
        assertEquals("萝卜", child.name)
        assertEquals("萝卜", child.nickname)
        assertEquals(8, child.age)
    }

    // TaskTemplate Tests
    @Test
    fun `taskTemplate deserialization withSerializedName`() {
        val json = """{
            "id": 1,
            "child_id": 1,
            "weekday": 1,
            "title": "阅读",
            "type": "reading",
            "description": "读一本书",
            "points": 10,
            "sort_order": 1
        }"""
        val template = gson.fromJson(json, TaskTemplate::class.java)
        assertEquals(1, template.id)
        assertEquals(1, template.childId)
        assertEquals(1, template.weekday)
        assertEquals("阅读", template.title)
        assertEquals("reading", template.type)
        assertEquals(10, template.points)
        assertEquals(1, template.sortOrder)
    }

    // TemplatesByWeekday Tests
    @Test
    fun `templatesByWeekday deserialization`() {
        val json = """{
            "weekday": 1,
            "weekday_name": "周一",
            "templates": []
        }"""
        val result = gson.fromJson(json, TemplatesByWeekday::class.java)
        assertEquals(1, result.weekday)
        assertEquals("周一", result.weekdayName)
        assertTrue(result.templates.isEmpty())
    }

    // DailyTask Tests
    @Test
    fun `dailyTask deserialization`() {
        val json = """{
            "id": 1,
            "child_id": 1,
            "date": "2026-05-22",
            "title": "阅读任务",
            "type": "reading",
            "points": 10,
            "status": "pending",
            "completed_at": null,
            "completed_by": null,
            "is_conditional": false,
            "is_adhoc": false,
            "photos": []
        }"""
        val task = gson.fromJson(json, DailyTask::class.java)
        assertEquals(1, task.id)
        assertEquals(1, task.childId)
        assertEquals("2026-05-22", task.date)
        assertEquals("阅读任务", task.title)
        assertEquals("reading", task.type)
        assertEquals(10, task.points)
        assertEquals("pending", task.status)
        assertNull(task.completedAt)
        assertNull(task.completedBy)
        assertFalse(task.isConditional)
        assertFalse(task.isAdhoc)
        assertTrue(task.photos.isEmpty())
    }

    @Test
    fun `dailyTask with completed status`() {
        val json = """{
            "id": 2,
            "child_id": 1,
            "date": "2026-05-22",
            "title": "写字任务",
            "type": "written",
            "points": 15,
            "status": "done",
            "completed_at": "2026-05-22T10:30:00",
            "completed_by": 1,
            "completed_by_username": "baba",
            "is_conditional": false,
            "is_adhoc": false,
            "photos": []
        }"""
        val task = gson.fromJson(json, DailyTask::class.java)
        assertEquals("done", task.status)
        assertNotNull(task.completedAt)
        assertEquals(1, task.completedBy)
        assertEquals("baba", task.completedByUsername)
    }

    // CheckInPhoto Tests
    @Test
    fun `checkInPhoto deserialization`() {
        val json = """{
            "id": 1,
            "photo_url": "/photos/1/2026-05-22/abc.jpg",
            "uploaded_by": 1,
            "uploaded_at": "2026-05-22T10:30:00",
            "reviewed": true,
            "review_note": "做得好"
        }"""
        val photo = gson.fromJson(json, CheckInPhoto::class.java)
        assertEquals(1, photo.id)
        assertEquals("/photos/1/2026-05-22/abc.jpg", photo.photoUrl)
        assertEquals(1, photo.uploadedBy)
        assertTrue(photo.reviewed)
        assertEquals("做得好", photo.reviewNote)
    }

    // ProgressResponse Tests
    @Test
    fun `progressResponse deserialization`() {
        val json = """{
            "child_id": 1,
            "date": "2026-05-22",
            "total_tasks": 5,
            "completed_tasks": 3,
            "today_points": 30,
            "cumulative_points": 100,
            "tasks": []
        }"""
        val progress = gson.fromJson(json, ProgressResponse::class.java)
        assertEquals(1, progress.childId)
        assertEquals("2026-05-22", progress.date)
        assertEquals(5, progress.totalTasks)
        assertEquals(3, progress.completedTasks)
        assertEquals(30, progress.todayPoints)
        assertEquals(100, progress.cumulativePoints)
    }

    // Reward Tests
    @Test
    fun `reward deserialization`() {
        val json = """{
            "id": 1,
            "title": "冰淇淋",
            "cost_points": 50,
            "description": "一个冰淇淋",
            "image_url": null
        }"""
        val reward = gson.fromJson(json, Reward::class.java)
        assertEquals(1, reward.id)
        assertEquals("冰淇淋", reward.title)
        assertEquals(50, reward.costPoints)
        assertEquals("一个冰淇淋", reward.description)
        assertNull(reward.imageUrl)
    }

    // VoiceParsedIntent Tests
    @Test
    fun `voiceParsedIntent deserialization`() {
        val json = """{
            "action": "create",
            "child": "萝卜",
            "weekday": 1,
            "title": "数学",
            "type": "written",
            "points": 10,
            "is_conditional": false
        }"""
        val intent = gson.fromJson(json, VoiceParsedIntent::class.java)
        assertEquals("create", intent.action)
        assertEquals("萝卜", intent.child)
        assertEquals(1, intent.weekday)
        assertEquals("数学", intent.title)
        assertEquals("written", intent.type)
        assertEquals(10, intent.points)
        assertFalse(intent.isConditional)
    }

    // PointBalance Tests
    @Test
    fun `pointBalance deserialization`() {
        val json = """{
            "child_id": 1,
            "balance": 100,
            "transactions": []
        }"""
        val balance = gson.fromJson(json, PointBalance::class.java)
        assertEquals(1, balance.childId)
        assertEquals(100, balance.balance)
        assertTrue(balance.transactions.isEmpty())
    }

    // PointTransaction Tests
    @Test
    fun `pointTransaction deserialization`() {
        val json = """{
            "id": 1,
            "child_id": 1,
            "amount": 10,
            "reason": "完成阅读任务",
            "related_task_id": 5,
            "created_at": "2026-05-22T10:30:00"
        }"""
        val transaction = gson.fromJson(json, PointTransaction::class.java)
        assertEquals(1, transaction.id)
        assertEquals(1, transaction.childId)
        assertEquals(10, transaction.amount)
        assertEquals("完成阅读任务", transaction.reason)
        assertEquals(5, transaction.relatedTaskId)
    }

    // InsightsResponse Tests
    @Test
    fun `insightsResponse deserialization`() {
        val json = """{
            "child_id": 1,
            "period": "week",
            "total_tasks": 20,
            "completed_tasks": 15,
            "completion_rate": 75.0,
            "total_points_earned": 150,
            "daily_stats": [],
            "completions_by_type": {"reading": 10, "written": 5},
            "streak": 3
        }"""
        val insights = gson.fromJson(json, InsightsResponse::class.java)
        assertEquals(1, insights.childId)
        assertEquals("week", insights.period)
        assertEquals(20, insights.totalTasks)
        assertEquals(15, insights.completedTasks)
        assertEquals(75.0f, insights.completionRate, 0.01f)
        assertEquals(150, insights.totalPointsEarned)
        assertEquals(3, insights.streak)
        assertEquals(10, insights.completionsByType["reading"])
        assertEquals(5, insights.completionsByType["written"])
    }

    // DailyStatItem Tests
    @Test
    fun `dailyStatItem deserialization`() {
        val json = """{"date":"2026-05-22","total":5,"completed":3,"points":30}"""
        val stat = gson.fromJson(json, DailyStatItem::class.java)
        assertEquals("2026-05-22", stat.date)
        assertEquals(5, stat.total)
        assertEquals(3, stat.completed)
        assertEquals(30, stat.points)
    }

    // TaskTemplateCreate Tests
    @Test
    fun `taskTemplateCreate serialization`() {
        val create = TaskTemplateCreate(
            weekday = 1,
            title = "阅读",
            type = "reading",
            description = "读一本书",
            points = 10,
            sortOrder = 1
        )
        val json = gson.toJson(create)
        assertTrue(json.contains("\"weekday\":1"))
        assertTrue(json.contains("\"title\":\"阅读\""))
        assertTrue(json.contains("\"type\":\"reading\""))
        assertTrue(json.contains("\"sort_order\":1"))
    }

    // TaskTemplateBatchCreate Tests
    @Test
    fun `taskTemplateBatchCreate serialization`() {
        val create = TaskTemplateBatchCreate(
            weekdays = listOf(1, 2, 3),
            title = "每日阅读",
            type = "reading"
        )
        val json = gson.toJson(create)
        assertTrue(json.contains("\"weekdays\":[1,2,3]"))
        assertTrue(json.contains("\"title\":\"每日阅读\""))
    }

    // ConditionalTaskCreate Tests
    @Test
    fun `conditionalTaskCreate serialization`() {
        val create = ConditionalTaskCreate(
            title = "额外任务",
            type = "reading",
            description = "完成快的孩子",
            points = 15,
            weekdays = "1,2,3"
        )
        val json = gson.toJson(create)
        assertTrue(json.contains("\"title\":\"额外任务\""))
        assertTrue(json.contains("\"weekdays\":\"1,2,3\""))
    }

    // RewardCreate Tests
    @Test
    fun `rewardCreate serialization`() {
        val create = RewardCreate(
            title = "冰淇淋",
            costPoints = 50,
            description = "一个冰淇淋"
        )
        val json = gson.toJson(create)
        assertTrue(json.contains("\"title\":\"冰淇淋\""))
        assertTrue(json.contains("\"cost_points\":50"))
    }

    // VoiceRequest Tests
    @Test
    fun `voiceRequest serialization`() {
        val request = VoiceRequest("给萝卜添加周一阅读任务")
        val json = gson.toJson(request)
        assertTrue(json.contains("\"text\":\"给萝卜添加周一阅读任务\""))
    }

    // ConditionalTask Tests
    @Test
    fun `conditionalTask deserialization`() {
        val json = """{
            "id": 1,
            "child_id": 1,
            "trigger_condition": "all_required_done",
            "title": "额外阅读",
            "type": "reading",
            "description": "完成快的孩子",
            "points": 15,
            "weekdays": "1,2,3"
        }"""
        val task = gson.fromJson(json, ConditionalTask::class.java)
        assertEquals(1, task.id)
        assertEquals(1, task.childId)
        assertEquals("all_required_done", task.triggerCondition)
        assertEquals("额外阅读", task.title)
        assertEquals("reading", task.type)
        assertEquals(15, task.points)
        assertEquals("1,2,3", task.weekdays)
    }

    // AdhocTaskCreate Tests
    @Test
    fun `adhocTaskCreate serialization`() {
        val create = AdhocTaskCreate(
            title = "临时任务",
            type = "reading",
            description = "临时添加",
            points = 5
        )
        val json = gson.toJson(create)
        assertTrue(json.contains("\"title\":\"临时任务\""))
        assertTrue(json.contains("\"type\":\"reading\""))
    }

    // AppVersion Tests
    @Test
    fun `appVersion deserialization`() {
        val json = """{
            "version_code": 10104,
            "version_name": "1.1.4",
            "apk_url": "/api/app/download/1.1.4",
            "apk_size": 1024000,
            "apk_md5": "abc123",
            "release_notes": "初始版本",
            "force_update": false,
            "min_supported_version": 10100
        }"""
        val version = gson.fromJson(json, AppVersion::class.java)
        assertEquals(10104, version.versionCode)
        assertEquals("1.1.4", version.versionName)
        assertFalse(version.forceUpdate)
        assertEquals(10100, version.minSupportedVersion)
    }
}
