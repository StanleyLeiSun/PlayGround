import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect(r'db_bak/kidscheck_20260601.db')
conn.row_factory = sqlite3.Row

# daily_task 表结构
cols = conn.execute("PRAGMA table_info([daily_task])").fetchall()
print("=== daily_task 表结构 ===")
for c in cols:
    print(f"  {c['name']:25s} {c['type']}")

# 最近 30 条
rows = conn.execute("SELECT * FROM [daily_task] ORDER BY id DESC LIMIT 30").fetchall()
print(f"\n=== 最近 30 条记录 ===")
print(f"{'ID':>4} {'child':>5} {'日期':12s} {'标题':15s} {'类型':8s} {'积分':>4} {'状态':8s} {'完成时间':25s} {'完成人':>5}")
print("-" * 100)
for r in rows:
    d = dict(r)
    date_str = str(d['date'])[:10] if d['date'] else ''
    title = d['title'] or ''
    status = d['status'] or ''
    completed_at = str(d['completed_at'])[:19] if d['completed_at'] else ''
    completed_by = d['completed_by'] or ''
    print(f"{d['id']:>4} {d['child_id']:>5} {date_str:12s} {title:15s} {d['type']:8s} {d['points']:>4} {status:8s} {completed_at:25s} {str(completed_by):>5}")

conn.close()
