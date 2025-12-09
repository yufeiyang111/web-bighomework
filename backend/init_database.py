"""
初始化数据库
运行此脚本以创建数据库和表
"""
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Zzw1zhengshui',
    'charset': 'utf8mb4'
}

# 读取SQL文件
with open('../database_schema.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# 分割SQL语句
sql_statements = []
current_statement = []

for line in sql_content.split('\n'):
    # 跳过注释和空行
    line = line.strip()
    if not line or line.startswith('--'):
        continue
    
    current_statement.append(line)
    
    # 如果遇到分号，表示一条语句结束
    if line.endswith(';'):
        sql_statements.append(' '.join(current_statement))
        current_statement = []

try:
    # 连接数据库（不指定database）
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    print("开始初始化数据库...")
    
    # 执行每条SQL语句
    for i, sql in enumerate(sql_statements):
        try:
            # 跳过USE语句，手动处理
            if sql.strip().upper().startswith('USE '):
                db_name = sql.split()[1].rstrip(';')
                connection.select_db(db_name)
                print(f"✓ 已切换到数据库: {db_name}")
            elif sql.strip().upper().startswith('CREATE DATABASE'):
                cursor.execute(sql)
                print(f"✓ 已创建数据库")
            elif sql.strip().upper().startswith('SHOW '):
                cursor.execute(sql)
                results = cursor.fetchall()
                print(f"✓ 数据库表: {results}")
            else:
                cursor.execute(sql)
                connection.commit()
                
                # 显示进度
                if sql.strip().upper().startswith('CREATE TABLE'):
                    table_name = sql.split()[5] if 'IF NOT EXISTS' in sql.upper() else sql.split()[2]
                    print(f"✓ 已创建表: {table_name}")
                elif sql.strip().upper().startswith('INSERT INTO'):
                    print(f"✓ 已插入数据")
                elif sql.strip().upper().startswith('CREATE INDEX'):
                    print(f"✓ 已创建索引")
                    
        except Exception as e:
            print(f"✗ 执行SQL失败: {str(e)[:100]}")
    
    print("\n数据库初始化完成！")
    
except Exception as e:
    print(f"✗ 数据库初始化失败: {e}")
finally:
    if 'connection' in locals():
        cursor.close()
        connection.close()
