import sys, os
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeDocument
from app.services.knowledge_base_service import knowledge_base_service
from app.config import INDEX_PATH

db = SessionLocal()
try:
    user_id = 2
    
    # Delete old index
    user_index_dir = os.path.join(str(INDEX_PATH), str(user_id))
    if os.path.exists(user_index_dir):
        import shutil
        shutil.rmtree(user_index_dir)
        print("Deleted old index")
    
    documents = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.user_id == user_id
    ).all()
    
    for doc in documents:
        doc.indexed_at = None
        doc.chunk_count = 0
    db.commit()
    
    # Index first document (Cxsy_v6.pdf - text based)
    for doc in documents:
        if 'Cxsy' in doc.filename:
            print(f"Indexing: {doc.filename}...")
            try:
                success = knowledge_base_service.index_document(db, user_id, doc.id)
                print(f"  Done! Chunks: {doc.chunk_count}")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
                db.rollback()
            break
    
    print("\nQuick index done. Will start OCR for scanned book separately.")
finally:
    db.close()