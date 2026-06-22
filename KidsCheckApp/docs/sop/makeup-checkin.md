# SOP: 补打卡（Makeup Check-in）

## 概述

当忘记打卡时，通过直接修改数据库来补打卡并增加积分。由于系统目前没有补打卡功能，需要手动操作数据库。

## 前置条件

- SSH 可免密登录线上服务器
- 了解需要补打卡的日期和孩子

## 数据库表结构

补打卡涉及 3 个表：

| 表名 | 作用 |
|------|------|
| `daily_task` | 每日任务，存储任务状态 |
| `point_transaction` | 积分流水，记录每次积分变动 |
| `point_account` | 积分账户，存储当前积分余额 |

## 用户 ID 对照表

| 用户 | ID |
|------|-----|
| 爸爸 | 1 |
| 妈妈 | 2 |
| 爷爷 | 3 |
| 奶奶 | 4 |
| 姥姥 | 5 |

## 操作步骤

### 1. 查询待补打的任务

```bash
ssh admin@47.94.167.238

# 查询指定孩子和日期的任务（注意日期格式）
sqlite3 -header -column /opt/kidscheck/backend/kidscheck_dev.db \
  "SELECT id, title, points, status FROM daily_task 
   WHERE child_id = <CHILD_ID> AND date = '<DATE> 00:00:00.000000';"
```

示例：
```bash
# 查询萝卜（child_id=1）在 2026-06-21 的任务
sqlite3 -header -column /opt/kidscheck/backend/kidscheck_dev.db \
  "SELECT id, title, points, status FROM daily_task 
   WHERE child_id = 1 AND date = '2026-06-21 00:00:00.000000';"
```

### 2. 查询当前积分余额

```bash
sqlite3 -header -column /opt/kidscheck/backend/kidscheck_dev.db \
  "SELECT balance FROM point_account WHERE child_id = <CHILD_ID>;"
```

### 3. 执行补打卡

根据第 1 步查询结果，替换 SQL 中的任务 ID 和积分值：

```bash
sqlite3 /opt/kidscheck/backend/kidscheck_dev.db << 'SQL'
BEGIN TRANSACTION;

-- 1. 更新任务状态为已完成
UPDATE daily_task 
SET status = 'done', completed_at = datetime('now'), completed_by = <USER_ID>
WHERE id IN (<TASK_ID_1>, <TASK_ID_2>, ...);

-- 2. 添加积分流水（每个任务一条记录）
INSERT INTO point_transaction (child_id, amount, reason, related_task_id, created_at)
VALUES (<CHILD_ID>, <POINTS_1>, 'task_completed', <TASK_ID_1>, datetime('now'));
INSERT INTO point_transaction (child_id, amount, reason, related_task_id, created_at)
VALUES (<CHILD_ID>, <POINTS_2>, 'task_completed', <TASK_ID_2>, datetime('now'));
-- ... 为每个任务添加一条记录

-- 3. 更新积分余额（原余额 + 新增积分）
UPDATE point_account SET balance = <NEW_BALANCE> WHERE child_id = <CHILD_ID>;

COMMIT;
SQL
```

### 4. 验证结果

```bash
# 验证任务状态
sqlite3 -header -column /opt/kidscheck/backend/kidscheck_dev.db \
  "SELECT id, title, status, completed_by, completed_at FROM daily_task 
   WHERE id IN (<TASK_ID_1>, <TASK_ID_2>, ...);"

# 验证积分余额
sqlite3 -header -column /opt/kidscheck/backend/kidscheck_dev.db \
  "SELECT balance FROM point_account WHERE child_id = <CHILD_ID>;"
```

## 完整示例

假设萝卜（child_id=1）在 2026-06-21 有 5 个任务需要补打，由爸爸（user_id=1）打卡：

```bash
ssh admin@47.94.167.238

# 查询任务
sqlite3 -header -column /opt/kidscheck/backend/kidscheck_dev.db \
  "SELECT id, title, points, status FROM daily_task 
   WHERE child_id = 1 AND date = '2026-06-21 00:00:00.000000';"

# 查询当前积分
sqlite3 -header -column /opt/kidscheck/backend/kidscheck_dev.db \
  "SELECT balance FROM point_account WHERE child_id = 1;"

# 执行补打卡（假设任务 ID 是 333-337，积分分别是 2,1,3,2,2，当前积分 180）
sqlite3 /opt/kidscheck/backend/kidscheck_dev.db << 'SQL'
BEGIN TRANSACTION;

UPDATE daily_task 
SET status = 'done', completed_at = datetime('now'), completed_by = 1 
WHERE id IN (333, 334, 335, 336, 337);

INSERT INTO point_transaction (child_id, amount, reason, related_task_id, created_at)
VALUES (1, 2, 'task_completed', 333, datetime('now'));
INSERT INTO point_transaction (child_id, amount, reason, related_task_id, created_at)
VALUES (1, 1, 'task_completed', 334, datetime('now'));
INSERT INTO point_transaction (child_id, amount, reason, related_task_id, created_at)
VALUES (1, 3, 'task_completed', 335, datetime('now'));
INSERT INTO point_transaction (child_id, amount, reason, related_task_id, created_at)
VALUES (1, 2, 'task_completed', 336, datetime('now'));
INSERT INTO point_transaction (child_id, amount, reason, related_task_id, created_at)
VALUES (1, 2, 'task_completed', 337, datetime('now'));

UPDATE point_account SET balance = 190 WHERE child_id = 1;

COMMIT;
SQL

# 验证
sqlite3 -header -column /opt/kidscheck/backend/kidscheck_dev.db \
  "SELECT id, title, status FROM daily_task WHERE id IN (333, 334, 335, 336, 337);"
sqlite3 -header -column /opt/kidscheck/backend/kidscheck_dev.db \
  "SELECT balance FROM point_account WHERE child_id = 1;"
```

## 注意事项

- **务必先查询再修改**，确认任务 ID 和积分值正确
- **使用事务**（BEGIN/COMMIT），出错可以回滚
- 积分计算公式：新余额 = 原余额 + 所有待补打任务的积分总和
- `completed_by` 字段记录谁执行的打卡操作
- 如果只想补打卡但不加积分，跳过步骤 2 和 3 中的积分相关 SQL

## 后续优化建议

开发补打卡 API，支持：
- 选择历史日期
- 选择要补打的任务
- 自动计算并添加积分
- 记录操作日志
