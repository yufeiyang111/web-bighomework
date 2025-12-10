"""
修复管理员密码的脚本
用于修复数据库中密码哈希格式不正确的问题
"""
from app import app, db
from models.user import User

with app.app_context():
    # 查找admin用户
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print(f'找到用户: {admin.username}')
        print(f'当前密码哈希: {admin.password_hash[:50] if admin.password_hash else "None"}...')
        
        # 重新设置密码
        admin.set_password('admin123')
        db.session.commit()
        
        print('[SUCCESS] 管理员密码已更新为: admin123')
        print(f'新密码哈希: {admin.password_hash[:50]}...')
        
        # 测试密码验证
        if admin.check_password('admin123'):
            print('[SUCCESS] 密码验证成功')
        else:
            print('[ERROR] 密码验证失败')
    else:
        # 创建新管理员
        admin = User(
            username='admin',
            email='admin@example.com',
            name='系统管理员',
            role='teacher',
            department='计算机科学系'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print('[SUCCESS] 创建新管理员用户')
        print('用户名: admin')
        print('密码: admin123')

