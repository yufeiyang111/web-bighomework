"""
成绩模型
"""
from datetime import datetime, timezone
from .base import db


class Score(db.Model):
    """成绩模型"""
    __tablename__ = 'scores'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8mb4',
        'mysql_collate': 'utf8mb4_unicode_ci'
    }

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=False)
    exam_id = db.Column(db.Integer, db.ForeignKey('exams.id'))
    subject = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)
    total_score = db.Column(db.Float, nullable=False)
    # 数据库中是生成列，避免插入时手动赋值
    percentage = db.Column(db.Float, db.Computed('(score / total_score) * 100', persisted=True))
    # 使用字符串枚举，保持与数据库定义一致（exam/manual/imported）
    type = db.Column(db.Enum('exam', 'manual', 'imported', name='scoretype'), default='manual')
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    comments = db.Column(db.Text)
    recorded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    # 生成列由数据库计算，不在 __init__ 手动赋值

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'class_id': self.class_id,
            'exam_id': self.exam_id,
            'subject': self.subject,
            'score': self.score,
            'total_score': self.total_score,
            'percentage': self.percentage,
            'type': self.type if isinstance(self.type, str) else (self.type.value if self.type else None),
            'recorded_by': self.recorded_by,
            'comments': self.comments,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }