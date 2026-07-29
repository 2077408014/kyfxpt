import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.services.knowledge_base_service import knowledge_base_service
from app.models.knowledge_base import KnowledgeDocument

db = SessionLocal()
try:
    user_id = 2
    
    status = knowledge_base_service.get_status(db, user_id)
    print(f"Index status: {status['index_size']} vectors, {status['document_count']} documents")
    
    docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.user_id == user_id).all()
    for doc in docs:
        print(f"\nDocument: {doc.filename}")
        print(f"  Chunks: {doc.chunk_count}, indexed_at: {doc.indexed_at}")
        print(f"  Subject: {doc.subject}")
    
    print("\n" + "="*60)
    print("Searching for '罚函数':")
    results = knowledge_base_service.search(user_id, "罚函数", top_k=5, threshold=0.0, enable_keyword_fallback=True)
    print(f"Found {len(results)} results")
    for i, r in enumerate(results):
        print(f"\n  Result {i+1}: similarity={r['similarity']:.4f}")
        print(f"  Content: {r['content'][:200]}")
        print(f"  Doc: {r['metadata'].get('filename')}")
    
    print("\n" + "="*60)
    print("Searching for '罚':")
    results2 = knowledge_base_service.search(user_id, "罚", top_k=5, threshold=0.0, enable_keyword_fallback=True)
    print(f"Found {len(results2)} results")
    for i, r in enumerate(results2):
        print(f"\n  Result {i+1}: similarity={r['similarity']:.4f}")
        print(f"  Content: {r['content'][:200]}")
    
    # Check if '罚函数' appears anywhere in the indexed content
    print("\n" + "="*60)
    print("Checking for '罚' character in index...")
    all_chunks = knowledge_base_service._get_all_chunks(user_id)
    count_with_fa = 0
    for chunk in all_chunks:
        if '罚' in chunk.get('content', ''):
            count_with_fa += 1
    print(f"Chunks containing '罚': {count_with_fa} / {len(all_chunks)}")
    
finally:
    db.close()