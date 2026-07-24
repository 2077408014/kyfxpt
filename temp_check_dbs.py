import sqlite3
import os
import datetime

dbs = [
    r'D:\软件\trae_cn\projects\KaoYanXT\kaoyan_xt.db',
    r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\kaoyan_xt.db',
    r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\kaoyan_xt.db',
    r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend\kaoyan_xt.db',
]

for db in dbs:
    if not os.path.exists(db):
        print(f'{db}: 不存在')
        continue
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        tables = cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t[0] for t in tables]
        stats = {}
        for t in table_names:
            try:
                cnt = cur.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
                stats[t] = cnt
            except:
                pass
        size_kb = os.path.getsize(db) // 1024
        mtime = os.path.getmtime(db)
        mt = datetime.datetime.fromtimestamp(mtime).strftime('%m-%d %H:%M')
        print(f'\n{db}')
        print(f'  大小: {size_kb}KB  修改时间: {mt}')
        print(f'  表: {stats}')
        conn.close()
    except Exception as e:
        print(f'{db}: 错误 {e}')
