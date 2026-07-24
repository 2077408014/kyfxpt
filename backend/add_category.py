import sqlite3

db_path = r'd:\软件\trae_cn\projects\KaoYanXT\kaoyan_xt.db'
conn = sqlite3.connect(db_path)

cursor = conn.execute("PRAGMA table_info(words)")
columns = [row[1] for row in cursor.fetchall()]
print(f"Current columns: {columns}")

if "category" not in columns:
    conn.execute("ALTER TABLE words ADD COLUMN category VARCHAR(20) DEFAULT 'CET-4'")
    conn.commit()
    print("Added category column")
    
    cursor = conn.execute("PRAGMA table_info(words)")
    columns = [row[1] for row in cursor.fetchall()]
    print(f"New columns: {columns}")
else:
    print("Category column already exists")

conn.close()