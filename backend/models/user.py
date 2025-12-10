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

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256))
    role = db.Column(db.String(20), nullable=False, default='student')  # teacher, student, admin
    name = db.Column(db.String(64))
    avatar = db.Column(db.String(200))
    department = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # 关系 - 使用字符串避免循环导入
    classes_taught = db.relationship('Class', backref='teacher', lazy='dynamic',
                                     foreign_keys='Class.teacher_id')
    created_courses = db.relationship('Course', backref='teacher', lazy='dynamic')
    created_exams = db.relationship('Exam', backref='teacher', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'name': self.name,
            'avatar': self.avatar,
            'department': self.department,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


class StudentClass(db.Model):
    """学生-班级关联表"""
    __tablename__ = 'student_classes'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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