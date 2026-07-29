import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeDocument

db = SessionLocal()
try:
    print("Documents:")
    docs = db.query(KnowledgeDocument).all()
    for doc in docs:
        print(f"  id={doc.id}, user_id={doc.user_id}, filename={doc.filename}")
        print(f"    chunk_count={doc.chunk_count}, indexed_at={doc.indexed_at}")
        print(f"    subject={doc.subject}")
        print(f"    storage_path={doc.storage_path}")
        print()
finally:
    db.close()