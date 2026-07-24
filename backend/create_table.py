import sqlite3
import os

db_path = r'd:\软件\trae_cn\projects\KaoYanXT\kaoyan_xt.db'
print(f'Database path: {db_path}')

conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor]
print(f'Existing tables: {tables}')

if 'password_reset_codes' not in tables:
    conn.execute("""
        CREATE TABLE password_reset_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            code VARCHAR(6) NOT NULL,
            expires_at DATETIME NOT NULL,
            used BOOLEAN NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    print('Table created successfully')
else:
    print('Table already exists')

conn.close()