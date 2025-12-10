"""
通知模型
"""
from datetime import datetime, timezone
from enum import Enum as PyEnum
from sqlalchemy import Enum
from .base import db


class NotificationType(PyEnum):
    EXAM_PUBLISHED = 'exam_published'
    EXAM_REMINDER = 'exam_reminder'
    SCORE_RELEASED = 'score_released'
    SYSTEM = 'system'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(Enum('exam_published', 'exam_reminder', 'score_released', 'system', name='notificationtype'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    related_id = db.Column(db.Integer)  # 关联的ID（如考试ID）
    related_type = db.Column(db.String(50))  # 关联类型（如'exam'）
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    read_at = db.Column(db.DateTime)

    # 关系
    user = db.relationship('User', backref='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type if isinstance(self.type, str) else self.type.value if hasattr(self.type, 'value') else str(self.type),
            'title': self.title,
            'content': self.content,
            'related_id': self.related_id,
            'related_type': self.related_type,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'read_at': self.read_at.isoformat() if self.read_at else None
        }

