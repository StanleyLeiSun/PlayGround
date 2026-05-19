import sqlite3
conn = sqlite3.connect('kidscheck.db')
rows = conn.execute('SELECT id, username, password_hash, role FROM user').fetchall()
for r in rows:
    print(f"id={r[0]} username={r[1]!r} pwd={r[2]!r} role={r[3]}")
print()
# Try login with Chinese username
row = conn.execute("SELECT id FROM user WHERE username = ? AND password_hash = ?", ('爸爸', '123456')).fetchone()
print(f"Login with 爸爸/123456: {'success' if row else 'failed'}")
