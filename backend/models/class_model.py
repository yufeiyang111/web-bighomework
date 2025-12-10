from datetime import datetime, timezone
from .base import db
from sqlalchemy import func


class Class(db.Model):
    __tablename__ = 'classes'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    max_students = db.Column(db.Integer, default=100)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    chat_room = db.relationship('ChatRoom', backref='class_', uselist=False)
    exams = db.relationship('Exam', backref='class_', lazy='dynamic')
    scores = db.relationship('Score', backref='class_', lazy='dynamic')

    @property
    def student_count(self):
        # 使用 SQLAlchemy 查询获取学生数量，更可靠
        from .user import StudentClass
        return db.session.query(func.count(StudentClass.id)).filter(
            StudentClass.class_id == self.id
        ).scalar() or 0

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'teacher_id': self.teacher_id,
            'course_id': self.course_id,
            'max_students': self.max_students,
            'student_count': self.student_count,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ChatRoom(db.Model):
    __tablename__ = 'chat_rooms'

    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False, unique=True)
    name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    messages = db.relationship('ChatMessage', backref='chat_room', lazy='dynamic')