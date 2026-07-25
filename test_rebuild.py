import sys, os
sys.path.insert(0, r'd:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend')
from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeDocument
from app.services.knowledge_base_service import knowledge_base_service

db = SessionLocal()

docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.user_id == 2).all()
for d in docs:
    print(f'Doc: id={d.id}, filename={d.filename}')
    print(f'  storage_path: {d.storage_path}')
    print(f'  exists: {os.path.exists(d.storage_path) if d.storage_path else "N/A"}')
    print(f'  chunk_count: {d.chunk_count}')
    print(f'  subject: {d.subject}')
    print()

print('Rebuilding index for user 2...')
knowledge_base_service._rebuild_index(db, 2)

status = knowledge_base_service.get_status(db, 2)
print(f'Status: docs={status["document_count"]}, chunks={status["total_chunks"]}, index_size={status["index_size"]}')

index_data = knowledge_base_service._load_index(2)
if index_data["index"] and index_data["index"].ntotal > 0:
    print(f'Index loaded: {index_data["index"].ntotal} vectors, {len(index_data["metadata"])} metadata entries')
    for m in index_data["metadata"][:3]:
        content = m.get("content", "")[:150]
        print(f'  [{m.get("filename")}] {content}...')
else:
    print('No index data!')

db.close()