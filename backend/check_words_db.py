import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'kaoyan_xt.db')
conn = sqlite3.connect(db_path)
cur = conn.cursor()

print("=== 用户词书单词 (user_id 不为空) ===")
cur.execute('SELECT word, phonetic, meaning FROM words WHERE user_id IS NOT NULL LIMIT 20')
rows = cur.fetchall()
for i, r in enumerate(rows):
    meaning_preview = (r[2][:60] + '...') if r[2] and len(r[2]) > 60 else (r[2] or '')
    print(f"{i+1}. word=[{r[0]}]  phonetic=[{r[1]}]")
    print(f"   meaning=[{meaning_preview}]")

print(f"\n总计: {len(rows)} 条用户词书数据")

print("\n=== 系统词书单词示例 (user_id 为空) ===")
cur.execute('SELECT word, phonetic, meaning FROM words WHERE user_id IS NULL LIMIT 5')
rows = cur.fetchall()
for i, r in enumerate(rows):
    print(f"{i+1}. word=[{r[0]}]  phonetic=[{r[1]}]  meaning=[{r[2][:40]}...]")

conn.close()
