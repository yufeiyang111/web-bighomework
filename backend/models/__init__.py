"""
数据库模型包 - 使用延迟导入解决循环依赖
"""
import sys
from typing import Dict, Type, Any

# 导入 db 和 Base
from .base import db, Base

# 创建一个字典来存储模型类
_MODEL_REGISTRY: Dict[str, Type[Base]] = {}


def _register_model(model_class: Type[Base]) -> Type[Base]:
    """注册模型类"""
    _MODEL_REGISTRY[model_class.__name__] = model_class
    return model_class


def get_model_class(model_name: str) -> Type[Base]:
    """获取模型类（延迟导入）"""
    if model_name not in _MODEL_REGISTRY:
        # 动态导入
        if model_name == 'User':
            from .user import User
            _MODEL_REGISTRY['User'] = User
        elif model_name == 'StudentClass':
            from .user import StudentClass
            _MODEL_REGISTRY['StudentClass'] = StudentClass
        elif model_name == 'Class':
            from .class_model import Class
            _MODEL_REGISTRY['Class'] = Class
        elif model_name == 'ChatRoom':
            from .class_model import ChatRoom
            _MODEL_REGISTRY['ChatRoom'] = ChatRoom
        elif model_name == 'Score':
            from .score import Score
            _MODEL_REGISTRY['Score'] = Score
        elif model_name == 'Course':
            from .course import Course
            _MODEL_REGISTRY['Course'] = Course
        elif model_name == 'Exam':
            from .exam import Exam
            _MODEL_REGISTRY['Exam'] = Exam
        # 可以继续添加其他模型...

    return _MODEL_REGISTRY.get(model_name)


# 创建方便的导入函数
def import_all_models():
    """导入所有模型，用于初始化"""
    # 这将在应用上下文中调用，确保所有模型都注册到 metadata
    from . import user, class_model, score, course, exam, question
    return {
        'User': user.User,
        'StudentClass': user.StudentClass,
        'Class': class_model.Class,
        'ChatRoom': class_model.ChatRoom,
        'Score': score.Score,
        'ScoreType': score.ScoreType,
        # 添加其他模型...
    }


# 为方便使用，提供直接导入
# 注意：这些导入可能导致循环，所以只在需要时使用
__all__ = [
    'db',
    'Base',
    'get_model_class',
    'import_all_models',
    # 不直接导出模型类，避免循环导入
]