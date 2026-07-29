import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.services.knowledge_base_service import knowledge_base_service
from app.services.rag_service import rag_service

db = SessionLocal()
try:
    user_id = 2
    
    status = knowledge_base_service.get_status(db, user_id)
    print(f"Index: {status['index_size']} vectors, {status['document_count']} docs")
    for doc in status.get('documents', []):
        print(f"  {doc['filename']}: {doc.get('chunk_count', 0)} chunks, indexed={doc.get('indexed_at')}")
    
    queries = ["函数极限", "函数极限的题目", "函数极限的题", "极限的题目", "极限题", "函数的极限"]
    
    for q in queries:
        print(f"\n{'='*60}")
        print(f"Query: '{q}'")
        
        results = knowledge_base_service.search(user_id, q, top_k=5, threshold=0.0, enable_keyword_fallback=True)
        print(f"  Found {len(results)} results")
        for i, r in enumerate(results):
            print(f"  [{i+1}] sim={r['similarity']:.4f} | {r['content'][:100]}")
        
        if not results:
            print("  NO RESULTS! Testing individual search methods...")
            
            vec_results = knowledge_base_service._vector_search(user_id, q, 5, 0.0)
            print(f"  Vector search: {len(vec_results)} results")
            for i, r in enumerate(vec_results):
                print(f"    [{i+1}] sim={r['similarity']:.4f} | {r['content'][:80]}")
            
            kw_results = knowledge_base_service._keyword_search(q, None, 10, None)
            print(f"  Keyword search: {len(kw_results)} results")
            for i, r in enumerate(kw_results):
                print(f"    [{i+1}] sim={r['similarity']:.4f} | {r['content'][:80]}")
            
            # Also test the embedding directly
            from app.utils.embedding import get_text_embedder
            embedder = get_text_embedder()
            q_vec = embedder.embed_texts([q])[0]
            
            index_data = knowledge_base_service._load_index(user_id)
            if index_data["index"]:
                import numpy as np
                D, I = index_data["index"].search(np.array([q_vec]), 5)
                print(f"  FAISS raw search distances: {D[0]}")
                print(f"  FAISS raw search indices: {I[0]}")
                for idx in I[0]:
                    if idx < len(index_data["chunks"]):
                        chunk = index_data["chunks"][idx]
                        print(f"    idx={idx} | {chunk['content'][:100]}")
    
    print("\n" + "="*60)
    print("Checking '函数' and '极限' individual tokens in index...")
    index_data = knowledge_base_service._load_index(user_id)
    for i, chunk in enumerate(index_data.get("chunks", [])):
        content = chunk.get("content", "")
        if "函数" in content and "极限" in content:
            print(f"  chunk[{i}]: {content[:150]}")
            print()
            
finally:
    db.close()