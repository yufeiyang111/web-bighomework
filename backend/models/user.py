"""
用户模型
"""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# 注意：这里使用 from .. 来导入 db
# 或者直接从 models.base 导入
try:
    # 尝试相对导入
    from .base import db
except ImportError:
    # 如果失败，尝试绝对导入
    from models.base import db


class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    # 与数据库字段 user_id 对齐，属性仍可用 user.id 访问
    id = db.Column('user_id', db.Integer, primary_key=True)
    # 注意：数据库中可能没有 username 字段，只定义实际存在的字段
    # 使用 system_account 作为主要标识字段
    system_account = db.Column(db.String(64), unique=True, nullable=True, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=True)
    # 注意：数据库中可能使用 role_id 关联 roles 表，而不是直接的 role 字段
    # 这里不定义 role 字段，通过 relationship 或属性访问器获取
    role_id = db.Column(db.Integer, db.ForeignKey('roles.role_id'), nullable=True)
    real_name = db.Column(db.String(64), nullable=True)
    photo_url = db.Column(db.String(200), nullable=True)
    # 注意：以下字段可能在数据库中不存在，使用 @property 提供兼容性访问
    # department = db.Column(db.String(100), nullable=True)  # 移除，数据库中不存在
    # phone = db.Column(db.String(20), nullable=True)  # 移除，数据库中不存在
    is_approved = db.Column(db.Boolean, default=True, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=True)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=True)
    
    # 关系：关联 roles 表（如果存在）
    # 注意：Role 模型在 role.py 中定义，这里使用字符串引用避免循环导入
    # role_rel 关系在 Role 模型中定义，通过 backref 访问
    
    # 兼容性属性：提供 username 和 name 作为 system_account 和 real_name 的别名
    @property
    def username(self):
        return self.system_account or f'user_{self.id}'
    
    @property
    def name(self):
        return self.real_name or self.system_account or f'用户{self.id}'
    
    @property
    def avatar(self):
        return self.photo_url
    
    @property
    def is_active(self):
        return self.is_approved if self.is_approved is not None else True
    
    @property
    def department(self):
        """兼容性属性：返回 None（数据库中不存在此字段）"""
        return None
    
    @property
    def phone(self):
        """兼容性属性：返回 None（数据库中不存在此字段）"""
        return None
    
    @property
    def role(self):
        """通过 role_id 获取角色名称，如果无法获取则返回默认值"""
        # 如果可以直接查询 roles 表
        try:
            if hasattr(self, 'role_rel') and self.role_rel:
                return self.role_rel.role_name
            # 否则尝试通过 SQL 查询
            if self.role_id:
                from database import Database
                query = "SELECT role_name FROM roles WHERE role_id = %s"
                result = Database.execute_query(query, (self.role_id,), fetch_one=True)
                if result:
                    return result.get('role_name', 'student')
        except:
            pass
        # 默认返回 student
        return 'student'

    # 关系 - 使用字符串避免循环导入
    classes_taught = db.relationship('Class', backref='teacher', lazy='dynamic',
                                     foreign_keys='Class.teacher_id')
    created_courses = db.relationship('Course', backref='teacher', lazy='dynamic',
                                      foreign_keys='Course.teacher_id')
    created_exams = db.relationship('Exam', backref='teacher', lazy='dynamic',
                                    foreign_keys='Exam.teacher_id')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        # 安全获取字段值，兼容不同的数据库结构
        username = getattr(self, 'username', None) or getattr(self, 'system_account', None) or f'user_{self.id}'
        name = getattr(self, 'name', None) or getattr(self, 'real_name', None) or username
        avatar = getattr(self, 'avatar', None) or getattr(self, 'photo_url', None)
        is_active = getattr(self, 'is_active', None)
        if is_active is None:
            is_active = getattr(self, 'is_approved', True)
        
        # 安全获取 role，通过属性访问器
        role_value = 'student'  # 默认值
        try:
            role_value = self.role  # 使用属性访问器
        except:
            pass
        
        return {
            'id': self.id,
            'username': username,
            'system_account': getattr(self, 'system_account', None) or username,
            'email': self.email,
            'role': role_value,
            'name': name,
            'real_name': getattr(self, 'real_name', None) or name,
            'avatar': avatar,
            'photo_url': avatar,
            'department': getattr(self, 'department', None),
            'phone': getattr(self, 'phone', None),
            'is_active': is_active,
            'is_approved': is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        username = getattr(self, 'username', None) or getattr(self, 'system_account', None) or f'user_{self.id}'
        return f'<User {username}>'


class StudentClass(db.Model):
    """学生-班级关联表"""
    __tablename__ = 'student_classes'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    student = db.relationship('User', backref='class_memberships')
    class_ = db.relationship('Class', backref='student_memberships')

    # 注意：这里不能使用 __table_args__ 作为元组，要使用字典
    # 使用 SQLAlchemy 的 UniqueConstraint
    __table_args__ = (
        db.UniqueConstraint('student_id', 'class_id', name='unique_student_class'),
        {
            'mysql_engine': 'InnoDB',
            'mysql_charset': 'utf8mb4',
            'mysql_collate': 'utf8mb4_unicode_ci'
        }
    )