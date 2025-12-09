"""
初始化AI聊天机器人数据库表
"""

import pymysql
from config import Config

def init_chatbot_tables():
    """执行chatbot_schema.sql初始化数据库表"""
    try:
        # 连接数据库
        db_config = Config.DB_CONFIG.copy()
        db_config.pop('cursorclass', None)  # 移除cursorclass
        connection = pymysql.connect(**db_config)
        cursor = connection.cursor()
        
        print("正在初始化AI聊天机器人数据库表...")
        
        # 读取SQL文件
        with open('chatbot_schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 分割并执行SQL语句
        statements = sql_script.split(';')
        
        for statement in statements:
            statement = statement.strip()
            if statement:
                try:
                    cursor.execute(statement)
                    connection.commit()
                except Exception as e:
                    print(f"执行SQL时出错: {e}")
                    print(f"SQL: {statement[:100]}...")
        
        print("✅ AI聊天机器人数据库表初始化成功！")
        print("已创建表:")
        print("  - learning_materials (学习资料库)")
        print("  - chat_sessions (聊天会话)")
        print("  - chat_messages (聊天消息)")
        print("  - 示例学习资料已插入")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        raise

if __name__ == '__main__':
    init_chatbot_tables()
