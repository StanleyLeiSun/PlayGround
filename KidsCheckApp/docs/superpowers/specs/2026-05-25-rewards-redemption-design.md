# Rewards Redemption Feature Design Spec

## Overview

完善积分兑换功能的完整闭环。家长在奖励页面选择奖励并为指定孩子兑换，可选拍照记录兑现现场。兑换历史在同一页面展示，有照片的可点击查看大图。

## Target Users

- **家长（parent）**：创建/管理奖励、执行兑换操作、拍照留底
- **祖辈（grandparent）**：查看奖励列表和兑换历史（只读）

## 交互流程

```
家长进入奖励页面
  ├─ 顶部：各孩子当前积分
  ├─ 中间：奖励列表（家长可添加/删除，点"兑换"触发兑换流程）
  └─ 底部：兑换记录（按时间倒序）

兑换流程（ModalBottomSheet）：
  1. 选择孩子（如果只有一个孩子则自动选中）
  2. 显示该孩子当前积分 & 本次消耗积分
  3. 可选：拍照留底（拍照或从相册选择）
  4. 确认兑换 → 扣积分 → 保存记录 → 刷新页面
```

## Backend Changes

### Database Migration

`reward_redemption` 表新增字段：
- `photo_url`: String(500), nullable — 兑现照片路径

### Modified Endpoint

#### `POST /api/rewards/{reward_id}/redeem`

改为 multipart form 支持可选照片上传。

**Request:**
- `child_id`: int (form field)
- `photo`: UploadFile (optional)

**Logic:**
1. 验证奖励存在
2. 验证积分充足并扣减
3. 如有照片：压缩保存至 `uploads/photos/rewards/{child_id}/{uuid}.jpg`
4. 创建 RewardRedemption 记录（含 photo_url）
5. 返回兑换记录

**Response:**
```json
{
  "id": 1,
  "child_id": 1,
  "reward_id": 2,
  "points_spent": 50,
  "redeemed_at": "2026-05-25T10:00:00",
  "status": "pending",
  "photo_url": "/photos/rewards/1/uuid.jpg",
  "reward_title": "冰淇淋"
}
```

### New Endpoint

#### `GET /api/rewards/redemptions`

查询兑换历史。

**Query Parameters:**
- `child_id`: int (optional, 不传则返回所有孩子的记录)

**Response:**
```json
[
  {
    "id": 1,
    "child_id": 1,
    "child_name": "萝卜",
    "reward_id": 2,
    "reward_title": "冰淇淋",
    "points_spent": 50,
    "redeemed_at": "2026-05-25T10:00:00",
    "status": "fulfilled",
    "photo_url": "/photos/rewards/1/uuid.jpg"
  }
]
```

### Configuration

照片存储路径：`uploads/photos/rewards/{child_id}/{uuid}.jpg`
通过 nginx 已有的 `/photos/` alias 提供静态访问。

## Android Client Changes

### Data Model

`Models.kt` 新增：
```kotlin
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
```

### API Service

```kotlin
// 修改兑换接口为 multipart
@Multipart
@POST("/api/rewards/{rewardId}/redeem")
suspend fun redeemReward(
    @Path("rewardId") rewardId: Int,
    @Part("child_id") childId: RequestBody,
    @Part photo: MultipartBody.Part? = null
): Response<RewardRedemption>

// 新增：获取兑换历史
@GET("/api/rewards/redemptions")
suspend fun getRedemptions(
    @Query("child_id") childId: Int? = null
): Response<List<RewardRedemption>>
```

### UI: RewardsScreen 重写

**页面结构：**
1. **顶部积分卡片** — 各孩子积分余额（复用已有样式）
2. **奖励列表** — 每项显示名称、所需积分、兑换按钮（家长可见）、删除按钮（家长可见）
3. **兑换记录** — 标题 + LazyColumn，每项显示：奖励名、孩子名、积分、时间、照片缩略图

**兑换 BottomSheet：**
- 孩子选择器（多孩子时显示）
- 积分信息：当前 XX 分 → 兑换后 XX 分
- 拍照区域：拍照/相册按钮，选择后显示预览
- 确认兑换按钮

**兑换记录项：**
- 左侧：照片缩略图（48dp 圆角方形），无照片则显示礼物 icon
- 中间：奖励标题 + 孩子名 + 时间
- 右侧：-XX分
- 点击照片：`wx.previewImage` / Android 全屏大图预览

## API Endpoints Summary

| Feature | Endpoint | Method | Change |
|---------|----------|--------|--------|
| 兑换奖励 | `/api/rewards/{id}/redeem` | POST | 改为 multipart，加照片 |
| 兑换历史 | `/api/rewards/redemptions` | GET | 新增 |

## Out of Scope

- 孩子自助兑换（仅家长操作）
- 奖励图片上传（奖励本身不带图）
- 兑换审批流程（直接生效）
- 微信小程序端兑换（本次只做 Android）
