import sys
sys.path.insert(0, r'd:\软件\trae_cn\projects\KaoYanXT\.worktrees\feature-local-llm-deployment\backend')
from app.services.knowledge_base_service import knowledge_base_service

results = knowledge_base_service.search(1, '复化辛普森法', top_k=5, threshold=0.15, enable_keyword_fallback=True)
print(f'Found {len(results)} results')
for i, r in enumerate(results):
    sim = r["similarity"]
    source = r["metadata"].get("filename", "?")
    content = r['content'][:200]
    print(f'Result {i+1}: similarity={sim:.3f}, source={source}')
    print(f'  Content: {content}...')
    print()