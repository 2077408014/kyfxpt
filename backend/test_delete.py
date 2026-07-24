import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from app.services.knowledge_base_service import knowledge_base_service
from app.models.knowledge_base import KnowledgeDocument

db = SessionLocal()
try:
    user_id = 1

    # 查看当前文档列表
    docs = knowledge_base_service.get_documents(db, user_id)
    print(f"当前文档数: {len(docs)}")
    for d in docs:
        print(f"  id={d['id']}, filename={d['filename']}, subject={d.get('subject')}")

    if docs:
        # 尝试删除最后一个文档
        target_id = docs[-1]['id']
        target_name = docs[-1]['filename']
        print(f"\n尝试删除文档 id={target_id}, filename={target_name}")

        result = knowledge_base_service.remove_document(db, user_id, target_id)
        print(f"删除结果: {result}")

        # 验证
        docs_after = knowledge_base_service.get_documents(db, user_id)
        print(f"删除后文档数: {len(docs_after)}")

        # 确认被删文档不在列表中
        remaining_ids = [d['id'] for d in docs_after]
        if target_id not in remaining_ids:
            print(f"✅ 文档 id={target_id} 已成功删除")
        else:
            print(f"❌ 文档 id={target_id} 仍然存在")
    else:
        print("没有可删除的文档")

except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
