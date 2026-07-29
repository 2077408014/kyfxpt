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

def run_ocr_for_doc(doc, page_start=0, page_end=None):
    import fitz
    from app.utils.ocr_parse import ocr_parser
    
    if page_end is None:
        page_end = sys.maxsize
    
    pdf_path = doc.storage_path
    fitz_doc = fitz.open(pdf_path)
    total_pages = len(fitz_doc)
    page_end = min(page_end, total_pages)
    
    print(f"  OCR pages {page_start}-{page_end} of {total_pages}", flush=True)
    
    full_text = ""
    for page_num in range(page_start, page_end):
        page = fitz_doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8))
        img_bytes = pix.tobytes("png")
        page_text = ocr_parser._parse_image_bytes(img_bytes)
        if page_text and len(page_text.strip()) > 10:
            full_text += page_text + "\n\n"
        
        if (page_num - page_start + 1) % 20 == 0 or page_num == page_end - 1:
            elapsed = time.time()
            pages_done = page_num - page_start + 1
            eta = (page_end - page_num - 1) * 12 / 60
            print(f"  Page {page_num+1}/{page_end}, chars: {len(full_text)}, ETA: {eta:.0f}min", flush=True)
    
    fitz_doc.close()
    return full_text

def main():
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
            print(f"Processing: {doc.filename}", flush=True)
            
            file_ext = os.path.splitext(doc.filename)[1].lower()
            
            if file_ext == '.pdf':
                import fitz
                
                fitz_doc = fitz.open(doc.storage_path)
                sample_text = fitz_doc[0].get_text()
                has_text = bool(sample_text and sample_text.strip())
                fitz_doc.close()
                
                if has_text:
                    print("  Text-based PDF, extracting...", flush=True)
                    text = ocr_parser.parse_file(doc.storage_path)
                else:
                    cache_path = get_cache_path(doc.id)
                    if os.path.exists(cache_path):
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if data.get('complete'):
                            print(f"  Using cached text ({len(data['text'])} chars)", flush=True)
                            text = data['text']
                        else:
                            print("  Incomplete cache, running OCR...", flush=True)
                            text = run_ocr_for_doc(doc)
                            save_cache(doc.id, text)
                    else:
                        print("  Scanned PDF, running OCR (this takes time)...", flush=True)
                        text = run_ocr_for_doc(doc)
                        save_cache(doc.id, text)
                
                if text:
                    temp_path = doc.storage_path + '.ocr_result.txt'
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    
                    original_path = doc.storage_path
                    doc.storage_path = temp_path
                    
                    try:
                        success = knowledge_base_service.index_document(db, user_id, doc.id)
                        print(f"  Indexed: {doc.chunk_count} chunks", flush=True)
                    except Exception as e:
                        print(f"  Index error: {e}", flush=True)
                        import traceback
                        traceback.print_exc()
                        db.rollback()
                    
                    doc.storage_path = original_path
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    db.commit()
                else:
                    print("  No text extracted, skipping", flush=True)
            else:
                try:
                    success = knowledge_base_service.index_document(db, user_id, doc.id)
                    print(f"  Indexed: {doc.chunk_count} chunks", flush=True)
                except Exception as e:
                    print(f"  Error: {e}", flush=True)
                    db.rollback()
        
        print("\n=== ALL DONE! ===", flush=True)
    finally:
        db.close()

def save_cache(doc_id, text):
    cache_path = get_cache_path(doc_id)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump({'text': text, 'complete': True}, f, ensure_ascii=False)

if __name__ == '__main__':
    main()