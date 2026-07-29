import sys, os, json, time
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeDocument
from app.services.knowledge_base_service import knowledge_base_service
from app.config import INDEX_PATH

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'ocr_text')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(doc_id):
    return os.path.join(CACHE_DIR, f'doc_{doc_id}.json')

def main():
    db = SessionLocal()
    try:
        user_id = 2
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id
        ).all()
        
        target_doc = None
        for doc in documents:
            if '最优化' in doc.filename:
                target_doc = doc
                break
        
        if not target_doc:
            print("Target document not found!")
            return
        
        print(f"Processing: {target_doc.filename}")
        
        cache_path = get_cache_path(target_doc.id)
        
        if os.path.exists(cache_path):
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('complete'):
                print(f"Found cached text ({len(data['text'])} chars)")
                text = data['text']
            else:
                text = run_ocr_and_cache(target_doc, cache_path)
        else:
            text = run_ocr_and_cache(target_doc, cache_path)
        
        if text:
            temp_path = target_doc.storage_path + '.ocr_temp.txt'
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            original_path = target_doc.storage_path
            target_doc.storage_path = temp_path
            
            try:
                success = knowledge_base_service.index_document(db, user_id, target_doc.id)
                print(f"Indexed! Chunks: {target_doc.chunk_count}")
            except Exception as e:
                print(f"Index error: {e}")
                import traceback
                traceback.print_exc()
                db.rollback()
            
            target_doc.storage_path = original_path
            if os.path.exists(temp_path):
                os.remove(temp_path)
            db.commit()
        else:
            print("No text extracted!")
        
        print("Done!")
    finally:
        db.close()

def run_ocr_and_cache(doc, cache_path):
    import fitz
    from app.utils.ocr_parse import ocr_parser
    
    print("Starting OCR (this will take ~90 minutes for 478 pages)...")
    pdf_path = doc.storage_path
    fitz_doc = fitz.open(pdf_path)
    total_pages = len(fitz_doc)
    
    full_text = ""
    start_time = time.time()
    
    for page_num in range(total_pages):
        page = fitz_doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(0.8, 0.8))
        img_bytes = pix.tobytes("png")
        page_text = ocr_parser._parse_image_bytes(img_bytes)
        if page_text and len(page_text.strip()) > 10:
            full_text += page_text + "\n\n"
        
        if (page_num + 1) % 10 == 0 or page_num == total_pages - 1:
            elapsed = time.time() - start_time
            pages_done = page_num + 1
            pages_remaining = total_pages - pages_done
            avg_time = elapsed / pages_done
            eta = pages_remaining * avg_time / 60
            print(f"  Page {pages_done}/{total_pages}, {len(full_text)} chars, ETA: {eta:.0f}min", flush=True)
    
    fitz_doc.close()
    
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump({'text': full_text, 'complete': True}, f, ensure_ascii=False)
    
    print(f"OCR complete! {len(full_text)} chars cached")
    return full_text

if __name__ == '__main__':
    main()