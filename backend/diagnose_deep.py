import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.services.knowledge_base_service import knowledge_base_service
from app.utils.embedding import get_text_embedder
import numpy as np

db = SessionLocal()
try:
    user_id = 2
    
    index_data = knowledge_base_service._load_index(user_id)
    index = index_data["index"]
    metadata = index_data["metadata"]
    
    print(f"Index: {index.ntotal if index else 0} vectors")
    print(f"Metadata: {len(metadata)} entries")
    
    if metadata:
        print(f"\nFirst metadata entry keys: {list(metadata[0].keys())}")
        print(f"First entry sample:")
        for k, v in metadata[0].items():
            val_str = str(v)[:100]
            print(f"  {k}: {val_str}")
    
    print(f"\n{'='*60}")
    print("Search for '函数极限':")
    query = "函数极限"
    query_vector = get_text_embedder().embed_text(query)
    query_vector = np.array([query_vector])
    
    distances, indices = index.search(query_vector, 10)
    
    print(f"Distances: {distances[0]}")
    print(f"Indices: {indices[0]}")
    
    for i, idx in enumerate(indices[0]):
        if 0 <= idx < len(metadata):
            meta = metadata[idx]
            distance = distances[0][i]
            similarity = 1 / (1 + distance)
            print(f"\n  Top[{i}]: idx={idx}, dist={distance:.4f}, sim={similarity:.4f}")
            print(f"  Content: {meta.get('content', '')[:150]}")
            print(f"  Doc: {meta.get('filename', 'N/A')}")
        else:
            print(f"\n  Top[{i}]: idx={idx} OUT OF RANGE (metadata len={len(metadata)})")
    
    print(f"\n{'='*60}")
    print("Search for '函数极限的题目':")
    query2 = "函数极限的题目"
    query_vector2 = get_text_embedder().embed_text(query2)
    query_vector2 = np.array([query_vector2])
    
    distances2, indices2 = index.search(query_vector2, 10)
    
    print(f"Distances: {distances2[0]}")
    print(f"Indices: {indices2[0]}")
    
    for i, idx in enumerate(indices2[0]):
        if 0 <= idx < len(metadata):
            meta = metadata[idx]
            distance = distances2[0][i]
            similarity = 1 / (1 + distance)
            print(f"\n  Top[{i}]: idx={idx}, dist={distance:.4f}, sim={similarity:.4f}")
            print(f"  Content: {meta.get('content', '')[:150]}")
            print(f"  Doc: {meta.get('filename', 'N/A')}")
    
    print(f"\n{'='*60}")
    print("Checking for '极限' in metadata content:")
    limit_count = 0
    for i, meta in enumerate(metadata):
        content = meta.get('content', '')
        if '极限' in content:
            limit_count += 1
            if limit_count <= 5:
                print(f"  [{i}] doc={meta.get('filename','?')}: {content[:120]}")
    print(f"  Total metadata with '极限': {limit_count}")
    
    print(f"\n{'='*60}")
    print("Checking for '函数极限' in metadata content:")
    func_limit_count = 0
    for i, meta in enumerate(metadata):
        content = meta.get('content', '')
        if '函数极限' in content:
            func_limit_count += 1
            print(f"  [{i}] doc={meta.get('filename','?')}: {content[:200]}")
    if func_limit_count == 0:
        print("  NONE!")
    
    print(f"\n{'='*60}")
    print("Sample all metadata from doc_id that contains math content:")
    doc_ids_seen = {}
    for i, meta in enumerate(metadata):
        doc_id = meta.get('document_id')
        filename = meta.get('filename', '?')
        key = f"{doc_id}_{filename}"
        if key not in doc_ids_seen:
            doc_ids_seen[key] = []
        doc_ids_seen[key].append(meta)
    
    for key, metas in doc_ids_seen.items():
        doc_id = metas[0].get('document_id')
        filename = metas[0].get('filename')
        print(f"\n  doc_id={doc_id}, filename={filename}, chunks={len(metas)}")
        for j, m in enumerate(metas[:3]):
            print(f"    [{j}]: {m.get('content', '')[:120]}")
            
finally:
    db.close()