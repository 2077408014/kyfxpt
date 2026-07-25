import sys
sys.path.insert(0, r'd:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend')
from app.services.knowledge_base_service import knowledge_base_service
from app.database import SessionLocal
import json

db = SessionLocal()
status = knowledge_base_service.get_status(db, 1)
print('Status:', json.dumps({k: v for k, v in status.items() if k != 'documents'}, indent=2, default=str))

index_data = knowledge_base_service._load_index(1)
print(f'Index exists: {index_data["index"] is not None}')
print(f'Index type: {type(index_data["index"]).__name__ if index_data["index"] else "None"}')
print(f'Total vectors: {index_data["index"].ntotal if index_data["index"] else 0}')
print(f'Metadata count: {len(index_data["metadata"])}')

if index_data["metadata"]:
    print(f'\nFirst metadata sample:')
    m = index_data["metadata"][0]
    print(f'  filename: {m.get("filename")}')
    print(f'  chunk_index: {m.get("chunk_index")}')
    print(f'  content preview: {m.get("content", "")[:200]}...')

db.close()