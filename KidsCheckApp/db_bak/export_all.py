import sqlite3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect(r'db_bak/kidscheck_20260601.db')
conn.row_factory = sqlite3.Row

# 获取所有表
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()

output_lines = []
output_lines.append("# KidsCheck 数据库导出 (2026-06-01)\n")

for t in tables:
    table_name = t[0]
    output_lines.append(f"## {table_name}\n")

    # 表结构
    cols = conn.execute(f"PRAGMA table_info([{table_name}])").fetchall()
    col_names = [c['name'] for c in cols]
    col_types = {c['name']: c['type'] for c in cols}

    output_lines.append("### 表结构\n")
    output_lines.append("| 字段 | 类型 |")
    output_lines.append("|------|------|")
    for c in cols:
        output_lines.append(f"| {c['name']} | {c['type']} |")
    output_lines.append("")

    # 最近 30 条记录
    rows = conn.execute(f"SELECT * FROM [{table_name}] ORDER BY ROWID DESC LIMIT 30").fetchall()
    count = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]

    output_lines.append(f"### 数据 (最近 30 条，共 {count} 条)\n")

    if not rows:
        output_lines.append("*空表*\n")
        continue

    # 表头
    header = "| " + " | ".join(col_names) + " |"
    separator = "| " + " | ".join(["---"] * len(col_names)) + " |"
    output_lines.append(header)
    output_lines.append(separator)

    # 数据行
    for r in rows:
        d = dict(r)
        values = []
        for cn in col_names:
            v = d[cn]
            if v is None:
                values.append("")
            else:
                # 转字符串，处理换行和管道符
                s = str(v).replace("|", "\\|").replace("\n", " ")
                # 截断过长的字段
                if len(s) > 50:
                    s = s[:47] + "..."
                values.append(s)
        row_str = "| " + " | ".join(values) + " |"
        output_lines.append(row_str)

    output_lines.append("")

conn.close()

# 写入文件
with open(r'db_bak/kidscheck_20260601_export.md', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output_lines))

print(f"导出完成: db_bak/kidscheck_20260601_export.md")
print(f"共 {len(tables)} 张表")
