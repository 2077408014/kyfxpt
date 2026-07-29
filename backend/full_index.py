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
                from rapidocr_onnxruntime import RapidOCR
                
                fitz_doc = fitz.open(doc.storage_path)
                total_pages = len(fitz_doc)
                
                sample_page = fitz_doc[0]
                sample_text = sample_page.get_text()
                has_text = bool(sample_text and sample_text.strip())
                
                if has_text:
                    print("  Text-based PDF, extracting text...", flush=True)
                    full_text = ""
                    for page_num in range(total_pages):
                        page = fitz_doc[page_num]
                        text = page.get_text()
                        if text and text.strip():
                            full_text += text + "\n\n"
                        if (page_num+1) % 50 == 0:
                            print(f"    Page {page_num+1}/{total_pages}, {len(full_text)} chars", flush=True)
                    fitz_doc.close()
                else:
                    cache_path = get_cache_path(doc.id)
                    if os.path.exists(cache_path):
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if data.get('complete'):
                            print(f"  Using cached text ({len(data['text'])} chars)", flush=True)
                            full_text = data['text']
                            fitz_doc.close()
                        else:
                            print("  Incomplete cache, running OCR...", flush=True)
                            full_text = run_ocr(fitz_doc, total_pages, cache_path)
                    else:
                        print(f"  Scanned PDF, starting OCR for {total_pages} pages...", flush=True)
                        print(f"  Estimated time: {total_pages * 6 / 60:.0f} minutes", flush=True)
                        full_text = run_ocr(fitz_doc, total_pages, cache_path)
                
                if full_text:
                    temp_path = doc.storage_path + '.ocr_temp.txt'
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        f.write(full_text)
                    
                    original_path = doc.storage_path
                    doc.storage_path = temp_path
                    
                    try:
                        success = knowledge_base_service.index_document(db, user_id, doc.id)
                        print(f"  Indexed! Chunks: {doc.chunk_count}", flush=True)
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
                    print(f"  Indexed! Chunks: {doc.chunk_count}", flush=True)
                except Exception as e:
                    print(f"  Error: {e}", flush=True)
                    db.rollback()
        
        print("\n=== ALL DONE! ===", flush=True)
    finally:
        db.close()

def run_ocr(fitz_doc, total_pages, cache_path):
    import fitz
    import numpy as np
    from PIL import Image
    import io
    from rapidocr_onnxruntime import RapidOCR
    
    print("  Loading OCR engine...", flush=True)
    ocr = RapidOCR()
    print("  Engine loaded, starting OCR...", flush=True)
    
    full_text = ""
    start_time = time.time()
    
    for page_num in range(total_pages):
        page = fitz_doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        img_np = np.array(img)
        result, _ = ocr(img_np)
        
        if result:
            page_texts = [item[1] for item in result if item[2] > 0.55]
            if page_texts:
                full_text += "\n".join(page_texts) + "\n\n"
        
        if (page_num + 1) % 20 == 0 or page_num == total_pages - 1:
            elapsed = time.time() - start_time
            pages_done = page_num + 1
            avg = elapsed / pages_done
            eta = (total_pages - pages_done) * avg / 60
            print(f"  Page {pages_done}/{total_pages}, {len(full_text)} chars, ETA: {eta:.0f}min", flush=True)
    
    fitz_doc.close()
    
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump({'text': full_text, 'complete': True}, f, ensure_ascii=False)
    
    print(f"  OCR complete! {len(full_text)} chars cached", flush=True)
    return full_text

if __name__ == '__main__':
    main()