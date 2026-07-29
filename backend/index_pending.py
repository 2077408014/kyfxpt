import sys
import os
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeDocument
from app.services.knowledge_base_service import knowledge_base_service
from app.config import INDEX_PATH

def clear_and_index():
    db = SessionLocal()
    try:
        user_id = 2
        user_index_dir = os.path.join(str(INDEX_PATH), str(user_id))
        
        if os.path.exists(user_index_dir):
            import shutil
            shutil.rmtree(user_index_dir)
            print("Deleted old index directory", flush=True)
        
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id
        ).all()
        
        for doc in documents:
            doc.indexed_at = None
            doc.chunk_count = 0
        db.commit()
        print(f"Reset {len(documents)} documents", flush=True)
        
        for doc in documents:
            print(f"\nIndexing: {doc.filename} ({doc.file_size/1024/1024:.1f} MB)", flush=True)
            
            last_progress = [0]
            def progress_callback(progress, message):
                if progress != last_progress[0] and (progress % 10 == 0 or progress <= 10 or progress == 100):
                    last_progress[0] = progress
                    print(f"  {progress}% - {message}", flush=True)
            
            try:
                success = knowledge_base_service.index_document(
                    db, user_id, doc.id, progress_callback
                )
                if success:
                    print(f"  Done! Chunks: {doc.chunk_count}", flush=True)
                else:
                    print(f"  Failed", flush=True)
            except Exception as e:
                print(f"  Error: {e}", flush=True)
                import traceback
                traceback.print_exc()
                db.rollback()
        
        print("\n=== All done! ===", flush=True)
    finally:
        db.close()

if __name__ == '__main__':
    clear_and_index()