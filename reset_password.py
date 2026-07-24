import sqlite3
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=['bcrypt'])
new_password_hash = pwd_context.hash('newpassword123')

conn = sqlite3.connect(r'd:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\kaoyan_xt.db')
cursor = conn.cursor()

cursor.execute("UPDATE users SET password = ? WHERE email = '2077408014@qq.com'", (new_password_hash,))
conn.commit()

cursor.execute("SELECT email, password FROM users WHERE email = '2077408014@qq.com'")
print(cursor.fetchall())

conn.close()