"""
初始化私聊消息相关的数据库表
"""
import pymysql
import os

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'yu6670980506',
    'database': 'web_education_system',
    'charset': 'utf8mb4'
}

# 读取SQL文件
with open('message_schema.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# 分割SQL语句
sql_statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]

try:
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    print("开始初始化私聊消息表...")
    
    for sql in sql_statements:
        if sql.strip():
            try:
                cursor.execute(sql)
                connection.commit()
                if 'CREATE TABLE' in sql.upper():
                    print(f"✓ 表创建成功")
            except pymysql.err.OperationalError as e:
                if e.args[0] == 1050:  # Table already exists
                    print(f"✓ 表已存在，跳过")
                else:
                    print(f"✗ 执行失败: {e}")
            except Exception as e:
                print(f"✗ 执行失败: {e}")
    
    # 创建上传目录
    upload_dir = 'uploads/messages'
    os.makedirs(upload_dir, exist_ok=True)
    print(f"✓ 已创建上传目录: {upload_dir}")
    
    print("\n私聊消息表初始化完成！")
    
except Exception as e:
    print(f"✗ 初始化失败: {e}")
finally:
    if 'connection' in locals():
        cursor.close()
        connection.close()
