import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.services.knowledge_base_service import knowledge_base_service
from app.config import INDEX_PATH
import os, json

db = SessionLocal()
try:
    user_id = 2
    
    status = knowledge_base_service.get_status(db, user_id)
    
    index_data = knowledge_base_service._load_index(user_id)
    
    print(f"Total chunks: {len(index_data.get('chunks', []))}")
    print(f"Total vectors: {index_data['index'].ntotal if index_data['index'] else 0}")
    
    chunks = index_data.get('chunks', [])
    
    print(f"\n{'='*60}")
    print("Searching for chunks containing '极限':")
    for i, chunk in enumerate(chunks):
        content = chunk.get("content", "")
        if "极限" in content:
            print(f"\n  chunk[{i}] (doc_id={chunk.get('metadata',{}).get('document_id')}):")
            print(f"  {content[:200]}")
    
    print(f"\n{'='*60}")
    print("Searching for chunks containing '函数':")
    count = 0
    for i, chunk in enumerate(chunks):
        content = chunk.get("content", "")
        if "函数" in content:
            count += 1
            if count <= 10:
                print(f"\n  chunk[{i}] (doc_id={chunk.get('metadata',{}).get('document_id')}):")
                print(f"  {content[:150]}")
    print(f"\n  Total chunks with '函数': {count}")
    
    print(f"\n{'='*60}")
    print("Searching for chunks containing '函数极限':")
    found = 0
    for i, chunk in enumerate(chunks):
        content = chunk.get("content", "")
        if "函数极限" in content:
            found += 1
            print(f"\n  chunk[{i}] (doc_id={chunk.get('metadata',{}).get('document_id')}):")
            print(f"  {content[:200]}")
    if found == 0:
        print("  NONE FOUND!")
    
    print(f"\n{'='*60}")
    print("All unique document_ids in chunks:")
    doc_ids = set()
    for chunk in chunks:
        doc_id = chunk.get('metadata', {}).get('document_id')
        if doc_id:
            doc_ids.add(doc_id)
    for doc_id in sorted(doc_ids):
        doc_chunks = [c for c in chunks if c.get('metadata',{}).get('document_id') == doc_id]
        sample = doc_chunks[0]['content'][:100] if doc_chunks else ""
        print(f"  doc_id={doc_id}: {len(doc_chunks)} chunks")
        print(f"    Sample: {sample}...")
    
    print(f"\n{'='*60}")
    print("Sample chunks from the math book (doc_id that is NOT the Cxsy one):")
    for chunk in chunks:
        doc_id = chunk.get('metadata', {}).get('document_id')
        if doc_id and doc_id != 10:
            print(f"\n  doc_id={doc_id}:")
            print(f"  {chunk.get('content', '')[:200]}")
            break
            
finally:
    db.close()