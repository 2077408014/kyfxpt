import sys, os, time
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeDocument
from app.services.knowledge_base_service import knowledge_base_service
from app.utils.ocr_parse import ocr_parser
from app.config import INDEX_PATH

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'ocr_text')
os.makedirs(CACHE_DIR, exist_ok=True)

def main():
    db = SessionLocal()
    try:
        user_id = 2
        
        doc = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id,
            KnowledgeDocument.filename.contains("最优化")
        ).first()
        
        if not doc:
            print("Document not found!")
            return
        
        print(f"Processing: {doc.filename}", flush=True)
        print(f"  Storage: {doc.storage_path}", flush=True)
        
        cache_path = os.path.join(CACHE_DIR, f'doc_{doc.id}.txt')
        
        if os.path.exists(cache_path):
            print(f"  Using cached OCR text", flush=True)
            with open(cache_path, 'r', encoding='utf-8') as f:
                full_text = f.read()
            print(f"  Cached text size: {len(full_text)} chars", flush=True)
        else:
            print(f"  Starting OCR (scanned PDF, 478 pages)...", flush=True)
            print(f"  Estimated time: ~90 minutes (10-15 sec/page)", flush=True)
            print(f"  Please be patient...", flush=True)
            print("", flush=True)
            
            start_time = time.time()
            last_update = [time.time()]
            
            def progress_callback(progress, message):
                elapsed = time.time() - start_time
                if time.time() - last_update[0] > 30:
                    last_update[0] = time.time()
                    if progress > 0:
                        eta = elapsed / progress * (100 - progress) / 60
                        print(f"  [{progress}%] {message}, elapsed: {elapsed/60:.0f}min, ETA: {eta:.0f}min", flush=True)
                    else:
                        print(f"  [{progress}%] {message}, elapsed: {elapsed/60:.0f}min", flush=True)
            
            full_text = ocr_parser.parse_file(doc.storage_path, progress_callback)
            
            elapsed = time.time() - start_time
            print(f"  OCR complete! Time: {elapsed/60:.0f}min", flush=True)
            print(f"  Text size: {len(full_text)} chars", flush=True)
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"  Cached to: {cache_path}", flush=True)
        
        if not full_text:
            print("  No text extracted!", flush=True)
            return
        
        print(f"\n  Building index...", flush=True)
        
        temp_path = doc.storage_path + '.ocr_temp.txt'
        with open(temp_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        original_path = doc.storage_path
        doc.storage_path = temp_path
        
        try:
            success = knowledge_base_service.index_document(db, user_id, doc.id)
            print(f"  Index success! Chunks: {doc.chunk_count}", flush=True)
        except Exception as e:
            print(f"  Index error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            db.rollback()
        
        doc.storage_path = original_path
        if os.path.exists(temp_path):
            os.remove(temp_path)
        db.commit()
        
        print(f"\n=== DONE! ===", flush=True)
        print(f"Document: {doc.filename}", flush=True)
        print(f"Chunks indexed: {doc.chunk_count}", flush=True)
        
        print(f"\nTesting search for '罚函数':", flush=True)
        results = knowledge_base_service.search(user_id, "罚函数", top_k=3, threshold=0.0, enable_keyword_fallback=True)
        print(f"Found {len(results)} results:", flush=True)
        for i, r in enumerate(results):
            print(f"  {i+1}. similarity={r['similarity']:.4f}")
            print(f"     {r['content'][:120]}...", flush=True)
        
    finally:
        db.close()

if __name__ == '__main__':
    main()