from database import Database

print("=" * 80)
print("数据库知识库内容：")
print("=" * 80)

# 查询知识库
result = Database.execute_query('SELECT * FROM learning_materials', fetch_all=True)

if result:
    for r in result:
        print(f"\nID: {r['material_id']}")
        print(f"标题: {r['title']}")
        print(f"分类: {r['category']}")
        print(f"标签: {r['tags']}")
        print(f"内容预览: {r['content'][:100]}...")
        print("-" * 40)
    print(f"\n总计: {len(result)} 条知识")
else:
    print("知识库为空")

print("=" * 80)
