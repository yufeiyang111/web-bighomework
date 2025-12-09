"""
生成管理员密码哈希
运行此脚本以生成正确的密码哈希值
"""
from werkzeug.security import generate_password_hash

# 密码
password = "admin123"

# 生成哈希
password_hash = generate_password_hash(password, method='pbkdf2:sha256')

print("管理员密码哈希值：")
print(password_hash)
print("\n请将此哈希值更新到 database_schema.sql 文件中的管理员账户")
