import sys, os
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeDocument
from app.services.knowledge_base_service import knowledge_base_service
from app.config import INDEX_PATH
import shutil

def main():
    db = SessionLocal()
    try:
        user_id = 2
        
        user_index_dir = os.path.join(str(INDEX_PATH), str(user_id))
        if os.path.exists(user_index_dir):
            shutil.rmtree(user_index_dir)
            print("Deleted old index")
        
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id
        ).all()
        
        for doc in documents:
            doc.indexed_at = None
            doc.chunk_count = 0
        db.commit()
        print(f"Reset {len(documents)} documents")
        
        for doc in documents:
            print(f"\nProcessing: {doc.filename}")
            
            try:
                success = knowledge_base_service.index_document(db, user_id, doc.id)
                print(f"  Indexed! Chunks: {doc.chunk_count}")
            except Exception as e:
                print(f"  Error: {e}")
                import traceback
                traceback.print_exc()
                db.rollback()
        
        print("\n" + "="*60)
        print("Testing search:")
        
        queries = ["函数极限", "函数极限的题目", "极限的题目", "罚函数"]
        for q in queries:
            print(f"\nQuery: '{q}'")
            results = knowledge_base_service.search(user_id, q, top_k=3, threshold=0.05, enable_keyword_fallback=True)
            print(f"  Found {len(results)} results")
            for i, r in enumerate(results):
                print(f"  [{i+1}] sim={r['similarity']:.4f} | {r['content'][:100]}")
        
        print("\n=== ALL DONE! ===")
    finally:
        db.close()

if __name__ == '__main__':
    main()