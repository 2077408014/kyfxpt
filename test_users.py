import sys
sys.path.insert(0, r'd:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend')
from app.database import SessionLocal
from app.models.user import User
from app.models.knowledge_base import KnowledgeDocument

db = SessionLocal()

users = db.query(User).all()
for u in users:
    print(f'User: id={u.id}, username={u.username}')
    docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.user_id == u.id).count()
    print(f'  Documents: {docs}')

db.close()