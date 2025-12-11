"""检查群聊表是否存在"""
from database import Database

def check_tables():
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    tables = ['chat_groups', 'group_members', 'group_messages', 'group_message_reads']
    
    for table in tables:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        result = cursor.fetchone()
        if result:
            print(f"✓ 表 {table} 存在")
            # 查看表结构
            cursor.execute(f"DESCRIBE {table}")
            columns = cursor.fetchall()
            print(f"  字段: {[col['Field'] for col in columns]}")
        else:
            print(f"✗ 表 {table} 不存在")
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    check_tables()
