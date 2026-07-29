import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.services.knowledge_base_service import knowledge_base_service

db = SessionLocal()
try:
    status = knowledge_base_service.get_status(db, 2)
    print(f"Index status: {status['index_size']} vectors, {status['document_count']} documents")
    
    results = knowledge_base_service.search(2, "罚函数", top_k=3, threshold=0.05, enable_keyword_fallback=True)
    print(f"\nSearch results for '罚函数': {len(results)} results")
    for i, r in enumerate(results):
        print(f"  Result {i+1}: similarity={r['similarity']:.4f}")
        print(f"    Content: {r['content'][:100]}...")
        print(f"    Metadata: subject={r['metadata'].get('subject')}, doc_id={r['metadata'].get('document_id')}")
        print()
    
    # Also test search for content that exists in Cxsy_v6.pdf
    results2 = knowledge_base_service.search(2, "极限", top_k=3, threshold=0.05, enable_keyword_fallback=True)
    print(f"\nSearch results for '极限': {len(results2)} results")
    for i, r in enumerate(results2):
        print(f"  Result {i+1}: similarity={r['similarity']:.4f}")
        print(f"    Content: {r['content'][:100]}...")
finally:
    db.close()