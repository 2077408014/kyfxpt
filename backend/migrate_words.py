import sqlite3
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

conn = sqlite3.connect('../kaoyan_xt.db')
cursor = conn.cursor()

cursor.execute('PRAGMA table_info(words)')
columns = [col[1] for col in cursor.fetchall()]
print('Current columns:', columns)

if 'category' not in columns:
    cursor.execute("ALTER TABLE words ADD COLUMN category VARCHAR(20) DEFAULT 'CET-4'")
    conn.commit()
    print('Added category column')
else:
    print('category column already exists')

cursor.execute('PRAGMA table_info(words)')
columns = [col[1] for col in cursor.fetchall()]
print('Updated columns:', columns)

conn.close()