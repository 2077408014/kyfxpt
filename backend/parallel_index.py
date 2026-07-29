import sys, os, json, time
sys.path.insert(0, '.')

from multiprocessing import Pool, cpu_count
from app.database import SessionLocal
from app.models.knowledge_base import KnowledgeDocument
from app.services.knowledge_base_service import knowledge_base_service
from app.config import INDEX_PATH

CACHE_DIR = os.path.join(os.path.dirname(__file__), '..', 'cache', 'ocr_text')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_cache_path(doc_id):
    return os.path.join(CACHE_DIR, f'doc_{doc_id}.json')

def ocr_page(args):
    page_num, scale = args
    import fitz
    import numpy as np
    from PIL import Image
    import io
    from rapidocr_onnxruntime import RapidOCR
    
    ocr = RapidOCR()
    
    pdf_path = r'D:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend\uploads\2_20260727_185230_最优化理论与算法-陈宝林.pdf'
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale))
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    img_np = np.array(img)
    result, _ = ocr(img_np)
    doc.close()
    
    texts = []
    if result:
        texts = [item[1] for item in result if item[2] > 0.55]
    
    return page_num, '\n'.join(texts) if texts else ''

def main():
    db = SessionLocal()
    try:
        user_id = 2
        
        user_index_dir = os.path.join(str(INDEX_PATH), str(user_id))
        if os.path.exists(user_index_dir):
            import shutil
            shutil.rmtree(user_index_dir)
        
        documents = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.user_id == user_id
        ).all()
        
        for doc in documents:
            doc.indexed_at = None
            doc.chunk_count = 0
        db.commit()
        
        for doc in documents:
            print(f"Processing: {doc.filename}", flush=True)
            
            file_ext = os.path.splitext(doc.filename)[1].lower()
            
            if file_ext == '.pdf':
                import fitz
                
                fitz_doc = fitz.open(doc.storage_path)
                total_pages = len(fitz_doc)
                
                sample_page = fitz_doc[0]
                sample_text = sample_page.get_text()
                has_text = bool(sample_text and sample_text.strip())
                fitz_doc.close()
                
                if has_text:
                    print("  Text-based PDF, extracting text...", flush=True)
                    full_text = ""
                    fitz_doc = fitz.open(doc.storage_path)
                    for page_num in range(total_pages):
                        page = fitz_doc[page_num]
                        text = page.get_text()
                        if text and text.strip():
                            full_text += text + "\n\n"
                    fitz_doc.close()
                    
                    if full_text:
                        temp_path = doc.storage_path + '.ocr_temp.txt'
                        with open(temp_path, 'w', encoding='utf-8') as f:
                            f.write(full_text)
                        original_path = doc.storage_path
                        doc.storage_path = temp_path
                        success = knowledge_base_service.index_document(db, user_id, doc.id)
                        doc.storage_path = original_path
                        os.remove(temp_path)
                        db.commit()
                        print(f"  Indexed! Chunks: {doc.chunk_count}", flush=True)
                else:
                    cache_path = get_cache_path(doc.id)
                    if os.path.exists(cache_path):
                        with open(cache_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if data.get('complete'):
                            print(f"  Using cached text", flush=True)
                            full_text = data['text']
                            temp_path = doc.storage_path + '.ocr_temp.txt'
                            with open(temp_path, 'w', encoding='utf-8') as f:
                                f.write(full_text)
                            original_path = doc.storage_path
                            doc.storage_path = temp_path
                            success = knowledge_base_service.index_document(db, user_id, doc.id)
                            doc.storage_path = original_path
                            os.remove(temp_path)
                            db.commit()
                            print(f"  Indexed! Chunks: {doc.chunk_count}", flush=True)
                            continue
                    
                    print(f"  Scanned PDF, OCR for {total_pages} pages using parallel processing...", flush=True)
                    start_time = time.time()
                    
                    num_workers = min(4, cpu_count())
                    print(f"  Using {num_workers} parallel workers", flush=True)
                    
                    tasks = [(i, 0.7) for i in range(total_pages)]
                    
                    page_texts = {}
                    with Pool(num_workers) as pool:
                        for page_num, text in pool.imap_unordered(ocr_page, tasks):
                            page_texts[page_num] = text
                            done = len(page_texts)
                            if done % 20 == 0 or done == total_pages:
                                elapsed = time.time() - start_time
                                avg = elapsed / done
                                eta = (total_pages - done) * avg / 60
                                print(f"  Progress: {done}/{total_pages} pages, ETA: {eta:.0f}min", flush=True)
                    
                    full_text = ""
                    for i in range(total_pages):
                        if i in page_texts and page_texts[i]:
                            full_text += page_texts[i] + "\n\n"
                    
                    print(f"  OCR complete! {len(full_text)} chars", flush=True)
                    
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        json.dump({'text': full_text, 'complete': True}, f, ensure_ascii=False)
                    
                    if full_text:
                        temp_path = doc.storage_path + '.ocr_temp.txt'
                        with open(temp_path, 'w', encoding='utf-8') as f:
                            f.write(full_text)
                        original_path = doc.storage_path
                        doc.storage_path = temp_path
                        success = knowledge_base_service.index_document(db, user_id, doc.id)
                        doc.storage_path = original_path
                        os.remove(temp_path)
                        db.commit()
                        print(f"  Indexed! Chunks: {doc.chunk_count}", flush=True)
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

if __name__ == '__main__':
    main()