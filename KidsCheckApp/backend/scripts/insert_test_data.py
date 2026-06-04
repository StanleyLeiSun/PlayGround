"""
向 kidscheck_dev.db 插入丰富的测试数据。
运行方式: cd backend && .venv/bin/python scripts/insert_test_data.py
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = "kidscheck_dev.db"


def main():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = datetime.now()
    today = now.strftime("%Y-%m-%d")

    # ========== 0. 清理旧数据 ==========
    print("🧹 清理旧数据...")
    for table in [
        "action_log", "reward_redemption", "point_transaction",
        "point_account", "check_in_photo", "oral_recording",
        "daily_task", "conditional_task", "task_template", "reward",
    ]:
        c.execute(f"DELETE FROM {table}")

    # ========== 1. 任务模板 ==========
    print("📝 插入任务模板...")

    templates = [
        # 萝卜(child_id=1)
        # 周一(weekday=1)
        (1, 1, "语文阅读", "reading", "阅读课外书30分钟，摘抄好词好句", 5, 1),
        (1, 1, "数学练习", "written", "完成口算/应用题练习一页", 5, 2),
        (1, 1, "英语听读", "reading", "英语课文朗读+听力练习", 5, 3),
        (1, 1, "书法练习", "written", "硬笔书法练习20分钟", 5, 4),
        (1, 1, "英语口语：Animals", "oral", "看图说出图中动物的英文名称，练习英语口语发音", 10, 5),
        # 周二(weekday=2)
        (1, 2, "语文阅读", "reading", "阅读课外书30分钟，摘抄好词好句", 5, 1),
        (1, 2, "数学练习", "written", "完成口算/应用题练习一页", 5, 2),
        (1, 2, "英语口语：Colors", "oral", "用英语描述周围物品的颜色", 10, 5),
        # 周三(weekday=3)
        (1, 3, "语文阅读", "reading", "阅读课外书30分钟", 5, 1),
        (1, 3, "数学练习", "written", "完成数学练习", 5, 2),
        (1, 3, "英语听读", "reading", "英语听力练习", 5, 3),
        (1, 3, "英语口语：Food", "oral", "说出常见食物的英文名称", 10, 5),
        # 周四(weekday=4)
        (1, 4, "语文阅读", "reading", "阅读课外书30分钟", 5, 1),
        (1, 4, "书法练习", "written", "硬笔书法练习20分钟", 5, 2),
        # 周五(weekday=5)
        (1, 5, "数学练习", "written", "完成数学练习", 5, 1),
        (1, 5, "英语口语：Body Parts", "oral", "用英语说出身体部位的名称", 10, 2),
        # 周六(weekday=6)
        (1, 6, "语文阅读", "reading", "周末阅读一篇小故事", 5, 1),
        # 周日(weekday=7)
        (1, 7, "英语口语：Numbers", "oral", "用英语从1数到100", 10, 1),

        # 蚕豆(child_id=2)
        # 周一(weekday=1)
        (2, 1, "识字练习", "reading", "认识5个新汉字", 5, 1),
        (2, 1, "算术启蒙", "written", "10以内加减法练习", 5, 2),
        (2, 1, "绘本阅读", "reading", "和家长一起读一本绘本", 5, 3),
        # 周二(weekday=2)
        (2, 2, "识字练习", "reading", "认识5个新汉字", 5, 1),
        (2, 2, "算术启蒙", "written", "10以内加减法练习", 5, 2),
        # 周三(weekday=3)
        (2, 3, "识字练习", "reading", "认识5个新汉字", 5, 1),
        (2, 3, "绘本阅读", "reading", "和家长一起读一本绘本", 5, 2),
        # 周四(weekday=4)
        (2, 4, "算术启蒙", "written", "10以内加减法练习", 5, 1),
        (2, 4, "识字练习", "reading", "认识5个新汉字", 5, 2),
        # 周五(weekday=5)
        (2, 5, "绘本阅读", "reading", "周末读一本有趣的故事书", 5, 1),
    ]

    for t in templates:
        c.execute(
            "INSERT INTO task_template (child_id, weekday, title, type, description, points, sort_order) VALUES (?, ?, ?, ?, ?, ?, ?)",
            t,
        )

    # ========== 2. 条件任务 ==========
    print("📝 插入条件任务...")
    conditional_tasks = [
        (1, "all_required_done", "课外阅读扩展", "reading", "完成当天所有任务后，额外阅读15分钟课外书", 10, "1,2,3,4,5"),
        (1, "all_required_done", "自由绘画", "written", "周末完成所有任务后，可以自由绘画30分钟", 8, "6,7"),
        (2, "all_required_done", "听故事", "reading", "完成当天所有任务后，可以听一个睡前故事", 8, "1,2,3,4,5"),
    ]
    for ct in conditional_tasks:
        c.execute(
            "INSERT INTO conditional_task (child_id, trigger_condition, title, type, description, points, weekdays) VALUES (?, ?, ?, ?, ?, ?, ?)",
            ct,
        )

    # ========== 3. 生成每日任务 (过去7天 + 今天) ==========
    print("📝 生成每日任务...")

    # 读取模板，按 (child_id, weekday) 分组
    c.execute("SELECT id, child_id, weekday, title, type, description, points FROM task_template")
    all_templates = c.fetchall()
    template_map = {}  # (child_id, weekday) -> list of {id, title, type, desc, points}
    for row in all_templates:
        tmpl_id, child_id, weekday, title, ttype, desc, points = row
        key = (child_id, weekday)
        template_map.setdefault(key, []).append({
            "id": tmpl_id, "title": title, "type": ttype,
            "description": desc, "points": points,
        })

    # 读取条件任务
    c.execute("SELECT id, child_id, title, type, description, points, weekdays FROM conditional_task")
    all_conditionals = c.fetchall()
    conditional_map = {}  # child_id -> list of {title, type, desc, points, weekdays}
    for row in all_conditionals:
        ct_id, child_id, title, ttype, desc, points, weekdays_str = row
        conditional_map.setdefault(child_id, []).append({
            "title": title, "type": ttype, "description": desc,
            "points": points, "weekdays": [int(w) for w in weekdays_str.split(",")],
        })

    task_id = 1
    for days_ago in range(7, -1, -1):  # 7天前到今天
        date = now - timedelta(days=days_ago)
        date_str = date.strftime("%Y-%m-%d") + " 00:00:00.000000"
        weekday = date.isoweekday()
        is_today = (days_ago == 0)

        for child_id in [1, 2]:
            # 普通模板任务
            key = (child_id, weekday)
            if key in template_map:
                for idx, tmpl in enumerate(template_map[key]):
                    # 决定完成状态
                    if is_today:
                        is_done = (idx == 0)  # 今天只完成第一个
                    else:
                        is_done = (task_id % 3 != 0)  # 历史大部分完成

                    status = "done" if is_done else "pending"
                    completed_at = None
                    completed_by = None
                    if is_done:
                        hour = 9 + (task_id % 5)
                        completed_at = date.strftime("%Y-%m-%d") + f" {hour}:{30 if task_id % 2 else 15}:00.000000"
                        completed_by = 3  # 爷爷

                    oral_image_url = None
                    if tmpl["type"] == "oral":
                        topic = tmpl["title"].replace("英语口语：", "").lower()
                        oral_image_url = f"/photos/oral/sample/{topic}.jpg"

                    c.execute(
                        """INSERT INTO daily_task
                        (id, child_id, date, source_template_id, title, type, points,
                         status, completed_at, completed_by, is_conditional, is_adhoc,
                         description, created_by, oral_image_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, ?, NULL, ?)""",
                        (task_id, child_id, date_str, tmpl["id"],
                         tmpl["title"], tmpl["type"], tmpl["points"],
                         status, completed_at, completed_by,
                         tmpl["description"], oral_image_url),
                    )
                    task_id += 1

            # 条件任务
            if child_id in conditional_map:
                for ct in conditional_map[child_id]:
                    if weekday in ct["weekdays"]:
                        if is_today:
                            is_done = False  # 今天的条件任务一般 pending
                        else:
                            is_done = (task_id % 2 == 0)

                        status = "done" if is_done else "pending"
                        completed_at = None
                        completed_by = None
                        if is_done:
                            completed_at = date.strftime("%Y-%m-%d") + f" 16:{task_id % 50:02d}:00.000000"
                            completed_by = 3

                        c.execute(
                            """INSERT INTO daily_task
                            (id, child_id, date, source_template_id, title, type, points,
                             status, completed_at, completed_by, is_conditional, is_adhoc,
                             description, created_by)
                            VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?, ?, 1, 0, ?, NULL)""",
                            (task_id, child_id, date_str,
                             ct["title"], ct["type"], ct["points"],
                             status, completed_at, completed_by,
                             ct["description"]),
                        )
                        task_id += 1

    # 添加今天的临时任务(adhoc)
    c.execute(
        """INSERT INTO daily_task
        (id, child_id, date, source_template_id, title, type, points,
         status, completed_at, completed_by, is_conditional, is_adhoc,
         description, created_by)
        VALUES (?, ?, ?, NULL, ?, ?, ?, 'pending', NULL, NULL, 0, 1, ?, ?)""",
        (task_id, 1, today + " 00:00:00.000000",
         "复习生字", "written", 5,
         "复习本周学过的生字词", 1),
    )
    task_id += 1

    # ========== 4. 打卡照片 ==========
    print("📝 添加打卡照片...")
    c.execute("SELECT id, child_id, type FROM daily_task WHERE status='done'")
    done_tasks = c.fetchall()
    photo_id = 1
    for dt in done_tasks:
        dt_id, child_id, task_type = dt
        # 非oral任务添加照片
        if task_type != "oral":
            for j in range(1, (dt_id % 2) + 2):  # 1-2张
                c.execute(
                    """INSERT INTO check_in_photo
                    (id, daily_task_id, photo_url, uploaded_by, uploaded_at, reviewed, review_note)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (photo_id, dt_id,
                     f"/photos/{child_id}/2026-05/photo_{photo_id}.jpg",
                     3,  # 爷爷上传
                     "2026-05-" + f"{(dt_id % 28) + 1:02d}" + f" {(10 + j):02d}:30:00.000000",
                     1 if photo_id % 3 != 0 else 0,
                     "做得很好！👍" if photo_id % 3 != 0 else None),
                )
                photo_id += 1

    # ========== 5. 口语录音 ==========
    print("📝 添加口语录音...")
    c.execute("SELECT id, child_id FROM daily_task WHERE type='oral' AND status='done'")
    oral_done_tasks = c.fetchall()
    recording_id = 1
    for ot in oral_done_tasks:
        c.execute(
            """INSERT INTO oral_recording
            (id, daily_task_id, audio_url, duration, recorded_by, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (recording_id, ot[0],
             f"/recordings/{ot[1]}/2026-05/recording_{recording_id}.wav",
             30 + (recording_id * 7 % 60),  # 30-90秒
             3,  # 爷爷录制
             "2026-05-" + f"{(recording_id % 28) + 1:02d}" + " 11:00:00.000000"),
        )
        recording_id += 1

    # ========== 6. 积分 ==========
    print("📝 计算积分...")
    # 重新创建积分账户
    c.execute("INSERT OR IGNORE INTO point_account (child_id, balance) VALUES (1, 0)")
    c.execute("INSERT OR IGNORE INTO point_account (child_id, balance) VALUES (2, 0)")

    pt_id = 1
    # 已完成任务的积分
    c.execute("""
        SELECT id, child_id, points, completed_at
        FROM daily_task WHERE status='done' ORDER BY completed_at
    """)
    for row in c.fetchall():
        dt_id, child_id, points, completed_at = row
        c.execute(
            """INSERT INTO point_transaction
            (id, child_id, amount, reason, related_task_id, created_at)
            VALUES (?, ?, ?, 'task_completed', ?, ?)""",
            (pt_id, child_id, points, dt_id, completed_at),
        )
        c.execute("UPDATE point_account SET balance = balance + ? WHERE child_id = ?", (points, child_id))
        pt_id += 1

    # ========== 7. 奖励 ==========
    print("📝 添加奖励...")
    rewards = [
        ("看30分钟动画片", 30, "完成当天所有任务后可以看30分钟动画片"),
        ("买一个新玩具", 100, "攒够积分可以买一个自己喜欢的小玩具(50元以内)"),
        ("去公园玩", 50, "周末和家人一起去公园玩"),
        ("吃冰淇淋", 20, "完成当天任务可以吃一个冰淇淋"),
        ("周末爬山", 80, "和家人一起去爬山，亲近大自然"),
        ("买一本课外书", 40, "买一本自己喜欢的课外书"),
    ]
    reward_ids = []
    for r in rewards:
        c.execute("INSERT INTO reward (title, cost_points, description) VALUES (?, ?, ?)", r)
        reward_ids.append(c.lastrowid)

    # 萝卜兑换冰淇淋 (第4个奖励 = 吃冰淇淋)
    ice_cream_reward_id = reward_ids[3]
    c.execute("SELECT balance FROM point_account WHERE child_id = 1")
    luobo_balance = c.fetchone()[0]
    if luobo_balance >= 20:
        c.execute(
            """INSERT INTO reward_redemption
            (child_id, reward_id, points_spent, redeemed_at, status, photo_url)
            VALUES (1, ?, 20, '2026-05-25 15:00:00.000000', 'fulfilled', NULL)""",
            (ice_cream_reward_id,),
        )
        c.execute("UPDATE point_account SET balance = balance - 20 WHERE child_id = 1")
        c.execute(
            """INSERT INTO point_transaction
            (id, child_id, amount, reason, related_task_id, created_at)
            VALUES (?, 1, -20, 'reward_redemption', NULL, '2026-05-25 15:00:00.000000')""",
            (pt_id,),
        )
        pt_id += 1

    # 蚕豆兑换看动画片 (第1个奖励)
    cartoon_reward_id = reward_ids[0]
    c.execute("SELECT balance FROM point_account WHERE child_id = 2")
    candou_balance = c.fetchone()[0]
    if candou_balance >= 30:
        c.execute(
            """INSERT INTO reward_redemption
            (child_id, reward_id, points_spent, redeemed_at, status, photo_url)
            VALUES (2, ?, 30, '2026-05-28 17:00:00.000000', 'fulfilled', NULL)""",
            (cartoon_reward_id,),
        )
        c.execute("UPDATE point_account SET balance = balance - 30 WHERE child_id = 2")
        c.execute(
            """INSERT INTO point_transaction
            (id, child_id, amount, reason, related_task_id, created_at)
            VALUES (?, 2, -30, 'reward_redemption', NULL, '2026-05-28 17:00:00.000000')""",
            (pt_id,),
        )
        pt_id += 1

    # ========== 8. 操作日志 ==========
    print("📝 添加操作日志...")
    logs = [
        (1, 1, "login", "user", 1, None, "2026-05-26 09:00:00.000000"),
        (2, 3, "login", "user", 3, None, "2026-05-26 09:30:00.000000"),
        (3, 3, "check_in", "daily_task", 1, '{"photo_count": 2}', "2026-05-26 10:30:00.000000"),
        (4, 1, "create_template", "task_template", 1, None, "2026-05-26 10:00:00.000000"),
        (5, 3, "check_in", "daily_task", 2, '{"photo_count": 1}', "2026-05-27 14:30:00.000000"),
        (6, 3, "check_in", "daily_task", 3, '{"photo_count": 2}', "2026-05-27 14:37:00.000000"),
        (7, 1, "create_reward", "reward", 1, None, "2026-05-22 10:00:00.000000"),
        (8, 1, "redeem_reward", "reward", 4, '{"child_id": 1}', "2026-05-25 15:00:00.000000"),
        (9, 2, "redeem_reward", "reward", 1, '{"child_id": 2}', "2026-05-28 17:00:00.000000"),
        (10, 1, "login", "user", 1, None, "2026-06-01 08:00:00.000000"),
        (11, 3, "login", "user", 3, None, "2026-06-01 08:30:00.000000"),
        (12, 1, "login", "user", 1, None, today + " 07:30:00.000000"),
        (13, 3, "login", "user", 3, None, today + " 08:00:00.000000"),
    ]
    for log in logs:
        c.execute(
            """INSERT INTO action_log (id, user_id, action, target_type, target_id, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            log,
        )

    conn.commit()
    conn.close()

    # ========== 打印统计 ==========
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print("\n✅ 测试数据插入完成！最终统计：")
    for table in ["user", "child", "task_template", "conditional_task", "daily_task",
                   "check_in_photo", "oral_recording", "point_account", "point_transaction",
                   "reward", "reward_redemption", "action_log"]:
        c.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"  {table}: {c.fetchone()[0]} rows")

    # 积分余额
    c.execute("SELECT c.nickname, pa.balance FROM child c JOIN point_account pa ON c.id = pa.child_id")
    for r in c.fetchall():
        print(f"\n  💰 {r[0]} 积分余额: {r[1]}")

    # 今日任务概况
    c.execute("SELECT child_id, COUNT(*), SUM(CASE WHEN status='done' THEN 1 ELSE 0 END) FROM daily_task WHERE date LIKE ? GROUP BY child_id", (today + "%",))
    print("\n  📋 今日任务:")
    for r in c.fetchall():
        child_name = "萝卜" if r[0] == 1 else "蚕豆"
        print(f"    {child_name}: {r[2]}/{r[1]} 已完成")

    # 口语任务
    c.execute("SELECT COUNT(*) FROM daily_task WHERE type='oral'")
    print(f"\n  🗣️  口语任务总数: {c.fetchone()[0]}")
    c.execute("SELECT COUNT(*) FROM oral_recording")
    print(f"  🎤 口语录音总数: {c.fetchone()[0]}")

    conn.close()


if __name__ == "__main__":
    main()
