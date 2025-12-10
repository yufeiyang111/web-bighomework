from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Enum
from .base import db


class ExamStatus(PyEnum):
    DRAFT = 'draft'
    PUBLISHED = 'published'
    ONGOING = 'ongoing'
    ENDED = 'ended'
    
    @classmethod
    def from_string(cls, value):
        """从字符串创建枚举值"""
        if isinstance(value, cls):
            return value
        value_lower = value.lower() if value else None
        for status in cls:
            if status.value == value_lower:
                return status
        raise ValueError(f"Invalid status: {value}")


class Exam(db.Model):
    __tablename__ = 'exams'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # 可选主班级（兼容旧数据），真实发布班级存放在 exam_classes 关联表
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_bank_id = db.Column(db.Integer, db.ForeignKey('question_banks.id'))
    total_questions = db.Column(db.Integer, default=0)
    total_score = db.Column(db.Float, default=100.0)
    passing_score = db.Column(db.Float, default=60.0)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer)  # 分钟
    status = db.Column(Enum('draft', 'published', 'ongoing', 'ended', name='examstatus'), default='draft')
    scheduled_publish_time = db.Column(db.DateTime)  # 定时发布时间
    auto_grade = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    question_bank = db.relationship('QuestionBank', backref='exams')
    results = db.relationship('ExamResult', backref='exam', lazy='dynamic')
    exam_classes = db.relationship('ExamClass', backref='exam', cascade='all, delete-orphan', lazy='select')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'class_id': self.class_id,
            'teacher_id': self.teacher_id,
            'question_bank_id': self.question_bank_id,
            'class_ids': [ec.class_id for ec in self.exam_classes] if hasattr(self, 'exam_classes') else [],
            'total_questions': self.total_questions,
            'total_score': self.total_score,
            'passing_score': self.passing_score,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'status': self.status if isinstance(self.status, str) else (self.status.value if self.status else None),
            'scheduled_publish_time': self.scheduled_publish_time.isoformat() if self.scheduled_publish_time else None,
            'auto_grade': self.auto_grade,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class ExamClass(db.Model):
    __tablename__ = 'exam_classes'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id', ondelete='CASCADE'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    class_ref = db.relationship('Class', backref='exam_classes')


class QuestionBank(db.Model):
    __tablename__ = 'question_banks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # 关系
    teacher = db.relationship('User', backref='question_banks')
    questions = db.relationship('MCQQuestion', backref='question_bank', lazy='dynamic')

    @property
    def question_count(self):
        return self.questions.count()


class MCQQuestion(db.Model):
    __tablename__ = 'mcq_questions'

    id = db.Column(db.Integer, primary_key=True)
    question_bank_id = db.Column(db.Integer, db.ForeignKey('question_banks.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # A, B, C, D
    explanation = db.Column(db.Text)
    score = db.Column(db.Float, default=1.0)
    difficulty = db.Column(db.String(10), default='medium')  # easy, medium, hard
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'question_bank_id': self.question_bank_id,
            'content': self.content,
            'options': {
                'A': self.option_a,
                'B': self.option_b,
                'C': self.option_c,
                'D': self.option_d
            },
            'correct_option': self.correct_option,
            'explanation': self.explanation,
            'score': self.score,
            'difficulty': self.difficulty,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class ExamResult(db.Model):
    __tablename__ = 'exam_results'

    id = db.Column(db.Integer, primary_key=True)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    score = db.Column(db.Float, default=0.0)
    total_score = db.Column(db.Float)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    submitted_at = db.Column(db.DateTime)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    student = db.relationship('User', backref='exam_results')
    answers = db.relationship('StudentAnswer', backref='exam_result', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'exam_id': self.exam_id,
            'student_id': self.student_id,
            'score': self.score,
            'total_score': self.total_score,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StudentAnswer(db.Model):
    __tablename__ = 'student_answers'

    id = db.Column(db.Integer, primary_key=True)
    exam_result_id = db.Column(db.Integer, db.ForeignKey('exam_results.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('mcq_questions.id'), nullable=False)
    selected_option = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean)
    score = db.Column(db.Float, default=0.0)
    answered_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # 关系
    question = db.relationship('MCQQuestion', backref='student_answers')
    
    def to_dict(self):
        return {
            'id': self.id,
            'exam_result_id': self.exam_result_id,
            'question_id': self.question_id,
            'selected_option': self.selected_option,
            'is_correct': self.is_correct,
            'score': self.score,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None
        }