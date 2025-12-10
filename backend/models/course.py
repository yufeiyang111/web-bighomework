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
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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
    materials = db.relationship('CourseMaterial', backref='course', lazy='dynamic')
    assignments = db.relationship('Assignment', backref='course', lazy='dynamic')

    def to_dict(self):
        # 多对多班级
        classes = list(self.classes) if self.classes else []
        class_ids = [cls.id for cls in classes]
        class_count = len(classes)
        student_total = sum(cls.student_count for cls in classes)
        teacher_ids = [t.id for t in self.teachers] if self.teachers else []
        teacher_names = [t.name or t.username for t in self.teachers] if self.teachers else []
        # 兼容旧数据：如果多对多为空，退回创建者
        if not teacher_ids and self.teacher_id:
            creator = User.query.get(self.teacher_id)
            if creator:
                teacher_ids = [creator.id]
                teacher_names = [creator.name or creator.username]

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
            'material_count': self.materials.count(),
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
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class CourseMaterial(db.Model):
    __tablename__ = 'course_materials'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_type = db.Column(db.String(20))  # pdf, doc, video, link
    file_url = db.Column(db.String(500))
    file_size = db.Column(db.Integer)  # 字节
    download_count = db.Column(db.Integer, default=0)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    uploader = db.relationship('User', backref='uploaded_materials')

    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'name': self.name,
            'description': self.description,
            'file_type': self.file_type,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'download_count': self.download_count,
            'uploaded_by': self.uploaded_by,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None
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