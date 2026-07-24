import sqlite3

db_path = r'd:\软件\trae_cn\projects\KaoYanXT\kaoyan_xt.db'
conn = sqlite3.connect(db_path)

cursor = conn.execute("SELECT COUNT(*) FROM words")
print(f"Word count: {cursor.fetchone()[0]}")

cursor = conn.execute("SELECT id, word, category FROM words LIMIT 5")
print("Sample words:")
for row in cursor.fetchall():
    print(row)

cursor = conn.execute("SELECT COUNT(*) FROM user_words")
print(f"User words count: {cursor.fetchone()[0]}")

cursor = conn.execute("SELECT uw.user_id, uw.word_id, w.word FROM user_words uw JOIN words w ON uw.word_id = w.id LIMIT 5")
print("Sample user words:")
for row in cursor.fetchall():
    print(row)

conn.close()