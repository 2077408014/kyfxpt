import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.services.knowledge_base_service import knowledge_base_service

db = SessionLocal()
try:
    user_id = 2
    
    svc = knowledge_base_service
    
    print("Query simplification test:")
    test_queries = ["函数极限", "函数极限的题目", "函数极限的题", "极限的题目", "极限题", "罚函数"]
    for q in test_queries:
        simplified = svc._simplify_query(q)
        print(f"  '{q}' -> '{simplified}'")
    
    print("\n" + "="*60)
    print("Keyword search test for '函数极限' (simplified):")
    index_data = svc._load_index(user_id)
    metadata = index_data["metadata"]
    
    kw_results = svc._keyword_search("函数极限", metadata, 10, None)
    print(f"Found {len(kw_results)} keyword results:")
    for i, r in enumerate(kw_results):
        print(f"  [{i}] sim={r['similarity']:.4f} score={r.get('keyword_score', 0):.1f}")
        print(f"      {r['content'][:120]}")
        print(f"      Doc: {r['metadata'].get('filename','?')}")
        print()
    
    print("\n" + "="*60)
    print("Keyword search test for '函数极限的题目' (simplified -> '函数极限'):")
    kw_results2 = svc._keyword_search("函数极限", metadata, 10, None)
    print(f"Found {len(kw_results2)} keyword results:")
    for i, r in enumerate(kw_results2):
        print(f"  [{i}] sim={r['similarity']:.4f} score={r.get('keyword_score', 0):.1f}")
        print(f"      {r['content'][:120]}")
        print()
    
    print("\n" + "="*60)
    print("Keyword search for '极限':")
    kw_results3 = svc._keyword_search("极限", metadata, 10, None)
    print(f"Found {len(kw_results3)} keyword results:")
    for i, r in enumerate(kw_results3):
        print(f"  [{i}] sim={r['similarity']:.4f} score={r.get('keyword_score', 0):.1f}")
        print(f"      {r['content'][:120]}")
        print()
    
    print("\n" + "="*60)
    print("Keyword search for '函数':")
    kw_results4 = svc._keyword_search("函数", metadata, 10, None)
    print(f"Found {len(kw_results4)} keyword results:")
    for i, r in enumerate(kw_results4):
        print(f"  [{i}] sim={r['similarity']:.4f} score={r.get('keyword_score', 0):.1f}")
        print(f"      {r['content'][:120]}")
        print()
    
finally:
    db.close()