import os
import random
import string
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from database import Database
from config import Config

class UserService:
    """用户服务类"""
    
    @staticmethod
    def generate_system_account(role_name):
        """
        生成系统账号
        
        Args:
            role_name: 角色名称 (admin, teacher, student)
        
        Returns:
            str: 系统账号
        """
        prefix_map = {
            'admin': 'ADMIN',
            'teacher': 'T',
            'student': 'S'
        }
        prefix = prefix_map.get(role_name, 'U')
        
        # 查询该角色下最后一个账号
        query = """
        SELECT system_account FROM users 
        WHERE system_account LIKE %s 
        ORDER BY user_id DESC LIMIT 1
        """
        result = Database.execute_query(query, (f"{prefix}%",), fetch_one=True)
        
        if result:
            last_account = result['system_account']
            # 提取数字部分并加1
            try:
                number = int(last_account.replace(prefix, '')) + 1
            except:
                number = 1
        else:
            number = 1
        
        # 生成新账号（格式：前缀+6位数字）
        return f"{prefix}{number:06d}"
    
    @staticmethod
    def get_role_id(role_name):
        """获取角色ID"""
        query = "SELECT role_id FROM roles WHERE role_name = %s"
        result = Database.execute_query(query, (role_name,), fetch_one=True)
        return result['role_id'] if result else None
    
    @staticmethod
    def create_user(email, password, role_name, real_name=None, student_number=None, photo_file=None, roster_id=None):
        """
        创建用户
        
        Args:
            email: 邮箱
            password: 密码
            role_name: 角色名称
            real_name: 真实姓名
            student_number: 学号（学生专用）
            photo_file: 照片文件对象
            roster_id: 学生花名册ID（学生专用）
        
        Returns:
            dict: 包含成功状态和消息或用户信息
        """
        try:
            # 检查邮箱是否已存在
            check_query = "SELECT user_id FROM users WHERE email = %s"
            if Database.execute_query(check_query, (email,), fetch_one=True):
                return {'success': False, 'message': '邮箱已被注册'}
            
            # 如果是学生，验证roster_id并检查是否已注册
            if role_name == 'student' and roster_id:
                roster_check_query = "SELECT is_registered FROM student_roster WHERE roster_id = %s"
                roster_record = Database.execute_query(roster_check_query, (roster_id,), fetch_one=True)
                
                if not roster_record:
                    return {'success': False, 'message': '花名册记录不存在'}
                
                if roster_record['is_registered']:
                    return {'success': False, 'message': '该学生已注册过账号'}
            
            # 获取角色ID
            role_id = UserService.get_role_id(role_name)
            if not role_id:
                return {'success': False, 'message': '无效的角色'}
            
            # 生成系统账号
            system_account = UserService.generate_system_account(role_name)
            
            # 加密密码
            password_hash = generate_password_hash(password, method='pbkdf2:sha256')
            
            # 处理照片上传
            photo_url = None
            if photo_file:
                photo_url = UserService.save_photo(photo_file, system_account)
            
            # 插入用户数据
            insert_query = """
            INSERT INTO users 
            (system_account, email, password_hash, role_id, real_name, student_number, photo_url, is_verified, is_approved)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # 学生可以直接注册但需要验证，教师需要审核
            is_approved = True if role_name == 'student' else False
            
            user_id = Database.execute_query(
                insert_query,
                (system_account, email, password_hash, role_id, real_name, student_number, photo_url, False, is_approved),
                commit=True
            )
            
            # 如果是学生且提供了roster_id，更新花名册记录
            if role_name == 'student' and roster_id:
                update_roster_query = """
                UPDATE student_roster 
                SET is_registered = TRUE, registered_user_id = %s 
                WHERE roster_id = %s
                """
                Database.execute_query(update_roster_query, (user_id, roster_id), commit=True)
            
            # 如果是教师，创建审核记录
            if role_name == 'teacher':
                approval_query = """
                INSERT INTO teacher_approvals (user_id, approval_status)
                VALUES (%s, 'pending')
                """
                Database.execute_query(approval_query, (user_id,), commit=True)
            
            return {
                'success': True,
                'message': '注册成功' if role_name == 'student' else '注册成功，等待管理员审核',
                'user_id': user_id,
                'system_account': system_account
            }
        
        except Exception as e:
            print(f"创建用户失败: {str(e)}")
            return {'success': False, 'message': f'注册失败: {str(e)}'}
    
    @staticmethod
    def save_photo(photo_file, system_account):
        """
        保存用户照片
        
        Args:
            photo_file: 文件对象
            system_account: 系统账号
        
        Returns:
            str: 照片路径
        """
        try:
            # 创建上传目录
            upload_folder = Config.UPLOAD_FOLDER
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)
            
            # 获取文件扩展名
            filename = secure_filename(photo_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
            
            # 生成新文件名
            new_filename = f"{system_account}.{ext}"
            filepath = os.path.join(upload_folder, new_filename)
            
            # 保存文件
            photo_file.save(filepath)
            
            return filepath
        except Exception as e:
            print(f"保存照片失败: {str(e)}")
            return None
    
    @staticmethod
    def authenticate(email, password):
        """
        用户认证
        
        Args:
            email: 邮箱
            password: 密码
        
        Returns:
            dict: 包含认证结果和用户信息
        """
        try:
            query = """
            SELECT u.*, r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.email = %s
            """
            user = Database.execute_query(query, (email,), fetch_one=True)
            
            if not user:
                return {'success': False, 'message': '邮箱或密码错误'}
            
            # 验证密码
            if not check_password_hash(user['password_hash'], password):
                return {'success': False, 'message': '邮箱或密码错误'}
            
            # 检查账号是否激活
            if not user['is_active']:
                return {'success': False, 'message': '账号已被禁用'}
            
            # 检查邮箱是否已验证
            if not user['is_verified']:
                return {'success': False, 'message': '请先验证邮箱'}
            
            # 检查教师是否已审核
            if user['role_name'] == 'teacher' and not user['is_approved']:
                return {'success': False, 'message': '账号待审核，请等待管理员审核'}
            
            # 更新最后登录时间
            update_query = "UPDATE users SET last_login = %s WHERE user_id = %s"
            Database.execute_query(update_query, (datetime.now(), user['user_id']), commit=True)
            
            # 移除敏感信息
            user.pop('password_hash', None)
            
            return {'success': True, 'user': user}
        
        except Exception as e:
            print(f"认证失败: {str(e)}")
            return {'success': False, 'message': f'登录失败: {str(e)}'}
    
    @staticmethod
    def get_user_by_id(user_id):
        """根据用户ID获取用户信息"""
        query = """
        SELECT u.*, r.role_name
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        WHERE u.user_id = %s
        """
        user = Database.execute_query(query, (user_id,), fetch_one=True)
        if user:
            user.pop('password_hash', None)
        return user
    
    @staticmethod
    def get_user_by_system_account(system_account):
        """根据系统账号获取用户信息"""
        query = """
        SELECT u.*, r.role_name
        FROM users u
        JOIN roles r ON u.role_id = r.role_id
        WHERE u.system_account = %s
        """
        user = Database.execute_query(query, (system_account,), fetch_one=True)
        if user:
            user.pop('password_hash', None)
        return user
    
    @staticmethod
    def verify_email(email):
        """验证邮箱"""
        query = "UPDATE users SET is_verified = TRUE WHERE email = %s"
        Database.execute_query(query, (email,), commit=True)
        return True
    
    @staticmethod
    def get_user_permissions(user_id):
        """获取用户权限列表"""
        query = """
        SELECT p.permission_name, p.permission_description
        FROM users u
        JOIN role_permissions rp ON u.role_id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.permission_id
        WHERE u.user_id = %s
        """
        permissions = Database.execute_query(query, (user_id,), fetch_all=True)
        return [p['permission_name'] for p in permissions] if permissions else []
    
    @staticmethod
    def update_password(user_id, new_password):
        """修改密码"""
        password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        query = "UPDATE users SET password_hash = %s WHERE user_id = %s"
        Database.execute_query(query, (password_hash, user_id), commit=True)
        return True
    
    @staticmethod
    def get_pending_teachers():
        """获取待审核的教师列表"""
        query = """
        SELECT u.*, ta.approval_id, ta.created_at as application_time
        FROM users u
        JOIN teacher_approvals ta ON u.user_id = ta.user_id
        WHERE ta.approval_status = 'pending'
        ORDER BY ta.created_at ASC
        """
        return Database.execute_query(query, fetch_all=True)
    
    @staticmethod
    def approve_teacher(approval_id, admin_id, approved, note=None):
        """
        审核教师
        
        Args:
            approval_id: 审核记录ID
            admin_id: 管理员ID
            approved: 是否通过
            note: 审核备注
        """
        try:
            # 获取用户ID
            query = "SELECT user_id FROM teacher_approvals WHERE approval_id = %s"
            result = Database.execute_query(query, (approval_id,), fetch_one=True)
            
            if not result:
                return {'success': False, 'message': '审核记录不存在'}
            
            user_id = result['user_id']
            status = 'approved' if approved else 'rejected'
            
            # 更新审核状态
            update_approval = """
            UPDATE teacher_approvals 
            SET approval_status = %s, admin_id = %s, approval_note = %s
            WHERE approval_id = %s
            """
            Database.execute_query(update_approval, (status, admin_id, note, approval_id), commit=True)
            
            # 如果通过，更新用户审核状态
            if approved:
                update_user = "UPDATE users SET is_approved = TRUE WHERE user_id = %s"
                Database.execute_query(update_user, (user_id,), commit=True)
            
            return {'success': True, 'message': '审核完成'}
        
        except Exception as e:
            print(f"审核失败: {str(e)}")
            return {'success': False, 'message': f'审核失败: {str(e)}'}
