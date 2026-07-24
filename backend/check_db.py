import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WORKTREE_DIR = BASE_DIR
PROJECT_ROOT = WORKTREE_DIR.parent

print(f"BASE_DIR: {BASE_DIR}")
print(f"WORKTREE_DIR: {WORKTREE_DIR}")
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"DATABASE_PATH: {PROJECT_ROOT / 'kaoyan_xt.db'}")

db_path = PROJECT_ROOT / 'kaoyan_xt.db'
conn = sqlite3.connect(str(db_path))

cursor = conn.execute("SELECT * FROM password_reset_codes ORDER BY created_at DESC LIMIT 5")
print("Reset codes in correct DB:")
for row in cursor.fetchall():
    print(row)

conn.close()