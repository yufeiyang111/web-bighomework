from datetime import datetime, timezone
from .base import db
from .class_model import Class
from .user import User


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    semester = db.Column(db.String(20), nullable=False)  # 例如: "2023-2024-1"
    credit = db.Column(db.Float, default=3.0)
    hours_per_week = db.Column(db.Integer, default=3)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # 关系（多对多）
    course_classes = db.relationship('CourseClass', backref='course', cascade='all, delete-orphan',
                                     lazy='select', overlaps="course,classes")
    classes = db.relationship('Class', secondary='course_classes', lazy='select',
                              overlaps="course,course_classes,class_")
    teachers = db.relationship('User', secondary='course_teachers', lazy='select')
    # 注意：learning_materials 表可能没有 course_id 字段，所以不能使用外键关系
    # materials = db.relationship('CourseMaterial', backref='course', lazy='dynamic', foreign_keys='CourseMaterial.course_id')
    # 暂时移除这个关系，避免查询错误
    # 如果需要获取课程资料，可以通过其他方式查询
    assignments = db.relationship('Assignment', backref='course', lazy='dynamic')

    def to_dict(self):
        # 多对多班级
        classes = list(self.classes) if self.classes else []
        class_ids = [cls.id for cls in classes]
        class_count = len(classes)
        student_total = sum(cls.student_count for cls in classes)
        teacher_ids = [t.id for t in self.teachers] if self.teachers else []
        # 使用 getattr 安全访问字段，优先使用 name，然后是 real_name，最后是 system_account
        teacher_names = []
        if self.teachers:
            for t in self.teachers:
                name = getattr(t, 'name', None) or getattr(t, 'real_name', None) or getattr(t, 'system_account', None) or getattr(t, 'username', None) or f'用户{t.id}'
                teacher_names.append(name)
        # 兼容旧数据：如果多对多为空，退回创建者
        if not teacher_ids and self.teacher_id:
            creator = User.query.get(self.teacher_id)
            if creator:
                teacher_ids = [creator.id]
                creator_name = getattr(creator, 'name', None) or getattr(creator, 'real_name', None) or getattr(creator, 'system_account', None) or getattr(creator, 'username', None) or f'用户{creator.id}'
                teacher_names = [creator_name]

        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'teacher_id': self.teacher_id,
            'semester': self.semester,
            'credit': self.credit,
            'hours_per_week': self.hours_per_week,
            'class_count': class_count,
            'material_count': 0,  # 暂时返回 0，因为 learning_materials 表没有 course_id 字段
            # 'material_count': self.materials.count(),  # 暂时注释，因为表结构不匹配
            'assignment_count': self.assignments.count(),
            'student_count': student_total,
            'classes': class_ids,
            'teacher_ids': teacher_ids,
            'teacher_names': teacher_names,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class CourseClass(db.Model):
    __tablename__ = 'course_classes'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class CourseTeacher(db.Model):
    __tablename__ = 'course_teachers'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class CourseMaterial(db.Model):
    """
    课程资料模型
    说明：
    - 数据库实际表名为 learning_materials（保留原表名）
    - 主键列名为 material_id，这里映射为 id 以兼容现有代码
    - 为兼容原有字段，新增可为空的文件/课程关联字段
    """
    __tablename__ = 'learning_materials'

    id = db.Column('material_id', db.Integer, primary_key=True)
    # 保留原表字段
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100))
    tags = db.Column(db.String(255))
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # 注意：以下字段可能在数据库中不存在，使用 @property 提供兼容性访问
    # course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=True)  # 移除，数据库中不存在
    # name = db.Column(db.String(200))  # 移除，数据库中不存在
    # description = db.Column(db.Text)  # 移除，数据库中不存在
    # file_type = db.Column(db.String(20))  # 移除，数据库中不存在
    # file_url = db.Column(db.String(500))  # 移除，数据库中不存在
    # file_size = db.Column(db.Integer)  # 移除，数据库中不存在
    # download_count = db.Column(db.Integer, default=0)  # 移除，数据库中不存在
    # uploaded_by = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=True)  # 移除，数据库中不存在
    # uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))  # 移除，数据库中不存在

    # 关系
    # uploader = db.relationship('User', backref='uploaded_materials', foreign_keys=[uploaded_by])  # 移除，因为 uploaded_by 字段不存在

    # 兼容性属性
    @property
    def course_id(self):
        """兼容性属性：返回 None（数据库中不存在此字段）"""
        return None
    
    @property
    def name(self):
        """兼容性属性：返回 title"""
        return self.title
    
    @property
    def description(self):
        """兼容性属性：返回 content"""
        return self.content
    
    @property
    def file_type(self):
        """兼容性属性：返回 None"""
        return None
    
    @property
    def file_url(self):
        """兼容性属性：返回 None"""
        return None
    
    @property
    def file_size(self):
        """兼容性属性：返回 None"""
        return None
    
    @property
    def download_count(self):
        """兼容性属性：返回 0"""
        return 0
    
    @property
    def uploaded_by(self):
        """兼容性属性：返回 created_by"""
        return self.created_by
    
    @property
    def uploaded_at(self):
        """兼容性属性：返回 created_at"""
        return self.created_at

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'content': self.content,
            'category': self.category,
            'tags': self.tags,
            'name': self.name or self.title,
            'description': self.description,
            'file_type': self.file_type,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'download_count': self.download_count,
            'uploaded_by': self.uploaded_by or self.created_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    total_score = db.Column(db.Float, default=100.0)
    due_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'title': self.title,
            'description': self.description,
            'total_score': self.total_score,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }