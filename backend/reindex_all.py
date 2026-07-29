import sys
import os
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.user import User
from app.models.knowledge_base import KnowledgeDocument
from app.services.knowledge_base_service import knowledge_base_service
from app.config import INDEX_PATH

def clear_and_reindex():
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        for user in users:
            print(f"\n=== Processing user {user.id} ===", flush=True)
            
            documents = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.user_id == user.id
            ).all()
            
            if not documents:
                print(f"  No documents found", flush=True)
                continue
            
            print(f"  Found {len(documents)} documents", flush=True)
            
            # Delete existing index files
            user_index_dir = os.path.join(INDEX_PATH, str(user.id))
            if os.path.exists(user_index_dir):
                import shutil
                shutil.rmtree(user_index_dir)
                print(f"  Deleted old index directory", flush=True)
            
            # Reset all documents
            for doc in documents:
                doc.indexed_at = None
                doc.chunk_count = 0
            db.commit()
            print(f"  Reset document status", flush=True)
            
            # Re-index each document
            for doc in documents:
                print(f"  Re-indexing: {doc.filename}", flush=True)
                
                def progress_callback(progress, message):
                    if progress % 25 == 0 or progress == 100:
                        print(f"    Progress: {progress}% - {message}", flush=True)
                
                try:
                    success = knowledge_base_service.index_document(
                        db, user.id, doc.id, progress_callback
                    )
                    if success:
                        print(f"    Done! Chunks: {doc.chunk_count}", flush=True)
                    else:
                        print(f"    Failed", flush=True)
                except Exception as e:
                    print(f"    Error: {e}", flush=True)
                    import traceback
                    traceback.print_exc()
                    db.rollback()
            
            print(f"  User {user.id} complete!", flush=True)
        
        print("\n=== All documents re-indexed! ===", flush=True)
        
    except Exception as e:
        print(f"Error: {e}", flush=True)
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    print("Starting re-indexing with improved embedding...", flush=True)
    print("This may take a while for large documents.\n", flush=True)
    clear_and_reindex()
