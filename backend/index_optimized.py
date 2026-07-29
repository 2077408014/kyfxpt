import sys
import os
import json
import time
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeDocument
from app.services.knowledge_base_service import knowledge_base_service
from app.config import INDEX_PATH

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'ocr_text')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(doc_id):
    return os.path.join(CACHE_DIR, f'doc_{doc_id}.json')

def load_cached_text(doc_id):
    path = get_cache_path(doc_id)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if data.get('complete'):
            return data.get('text', '')
    return None

def save_cached_text(doc_id, text, complete=True):
    path = get_cache_path(doc_id)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump({'text': text, 'complete': complete}, f, ensure_ascii=False)

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
            print(f"\n{'='*60}", flush=True)
            print(f"Processing: {doc.filename} ({doc.file_size/1024/1024:.1f} MB)", flush=True)
            
            cached = load_cached_text(doc.id)
            if cached:
                print(f"  Using cached text ({len(cached)} chars)", flush=True)
                continue
            
            file_ext = os.path.splitext(doc.filename)[1].lower()
            
            if file_ext == '.pdf':
                import fitz
                from app.utils.ocr_parse import ocr_parser
                
                pdf_path = doc.storage_path
                fitz_doc = fitz.open(pdf_path)
                total_pages = len(fitz_doc)
                print(f"  PDF has {total_pages} pages", flush=True)
                
                sample_page = fitz_doc[0]
                sample_text = sample_page.get_text()
                has_text = bool(sample_text and sample_text.strip())
                
                if has_text:
                    print(f"  Text-based PDF, extracting text directly...", flush=True)
                    full_text = ""
                    for i, page in enumerate(fitz_doc):
                        text = page.get_text()
                        if text and text.strip():
                            full_text += text + "\n\n"
                        if (i+1) % 50 == 0:
                            print(f"    Extracted {i+1}/{total_pages} pages, {len(full_text)} chars so far", flush=True)
                    save_cached_text(doc.id, full_text)
                    print(f"  Saved {len(full_text)} chars to cache", flush=True)
                else:
                    print(f"  Scanned PDF, running OCR...", flush=True)
                    print(f"  This will take a while (~12s per page, ~{total_pages*12/60:.0f}min total)", flush=True)
                    
                    full_text = ""
                    batch_size = 10
                    batch_start = 0
                    
                    if os.path.exists(get_cache_path(doc.id) + '.progress'):
                        with open(get_cache_path(doc.id) + '.progress', 'r') as f:
                            batch_start = int(f.read().strip())
                        print(f"  Resuming from page {batch_start}", flush=True)
                    
                    for batch_start in range(0, total_pages, batch_size):
                        batch_end = min(batch_start + batch_size, total_pages)
                        batch_text = ""
                        
                        for page_num in range(batch_start, batch_end):
                            page = fitz_doc[page_num]
                            pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8))
                            img_bytes = pix.tobytes("png")
                            page_text = ocr_parser._parse_image_bytes(img_bytes)
                            if page_text and len(page_text.strip()) > 10:
                                batch_text += page_text + "\n\n"
                        
                        full_text += batch_text
                        
                        with open(get_cache_path(doc.id) + '.progress', 'w') as f:
                            f.write(str(batch_end))
                        
                        elapsed = (time.time() - start) if 'start' in dir() else 0
                        pages_done = batch_end
                        pages_remaining = total_pages - pages_done
                        eta = pages_remaining * 12 / 60
                        print(f"  Pages {batch_end}/{total_pages}, {len(full_text)} chars, ETA: {eta:.0f}min", flush=True)
                    
                    save_cached_text(doc.id, full_text)
                    progress_file = get_cache_path(doc.id) + '.progress'
                    if os.path.exists(progress_file):
                        os.remove(progress_file)
                    print(f"  OCR complete! Saved {len(full_text)} chars to cache", flush=True)
                
                fitz_doc.close()
            else:
                print(f"  Non-PDF file, will use standard parsing", flush=True)
        
        print("\n=== Text extraction complete, now indexing ===", flush=True)
        
        for doc in documents:
            cached = load_cached_text(doc.id)
            if cached:
                print(f"\nIndexing: {doc.filename}", flush=True)
                
                temp_storage = doc.storage_path + '.temp.txt'
                with open(temp_storage, 'w', encoding='utf-8') as f:
                    f.write(cached)
                
                original_path = doc.storage_path
                doc.storage_path = temp_storage
                
                try:
                    success = knowledge_base_service.index_document(
                        db, user_id, doc.id, None
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
                
                doc.storage_path = original_path
                if os.path.exists(temp_storage):
                    os.remove(temp_storage)
                db.commit()
            else:
                print(f"\nIndexing: {doc.filename} (no cached text, using standard parsing)", flush=True)
                try:
                    success = knowledge_base_service.index_document(
                        db, user_id, doc.id, None
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
        
        print("\n=== ALL DONE! ===", flush=True)
    finally:
        db.close()

if __name__ == '__main__':
    clear_and_index()