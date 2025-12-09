"""
初始化管理员账户
运行此脚本以更新数据库中的管理员密码
"""
import pymysql
from werkzeug.security import generate_password_hash

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'Zzw1zhengshui',
    'database': 'web_education_system',
    'charset': 'utf8mb4'
}

# 管理员密码
ADMIN_PASSWORD = 'admin123'

try:
    # 连接数据库
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    # 生成密码哈希
    password_hash = generate_password_hash(ADMIN_PASSWORD, method='pbkdf2:sha256')
    
    # 更新管理员密码
    sql = """
    UPDATE users 
    SET password_hash = %s 
    WHERE system_account = 'ADMIN000001'
    """
    
    cursor.execute(sql, (password_hash,))
    connection.commit()
    
    print("✓ 管理员账户初始化成功！")
    print(f"  邮箱: admin@system.com")
    print(f"  密码: {ADMIN_PASSWORD}")
    print(f"  系统账号: ADMIN000001")
    print("\n请在首次登录后立即修改密码！")
    
except Exception as e:
    print(f"✗ 初始化失败: {e}")
finally:
    if 'connection' in locals():
        cursor.close()
        connection.close()
