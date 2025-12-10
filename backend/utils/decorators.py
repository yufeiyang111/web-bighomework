"""
装饰器工具
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, get_jwt
from models.user import User


def teacher_required(f):
    """
    装饰器：要求用户必须是教师角色
    必须在 @jwt_required() 之后使用
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取当前用户ID（转换为整数）
        current_user_id_str = get_jwt_identity()
        if not current_user_id_str:
            return {'message': '未认证'}, 401
        
        current_user_id = int(current_user_id_str)
        
        # 从JWT中获取角色信息（如果存在）
        jwt_data = get_jwt()
        role = jwt_data.get('role')
        
        # 如果JWT中没有角色信息，从数据库查询
        if not role:
            user = User.query.get(current_user_id)
            if not user:
                return {'message': '用户不存在'}, 404
            role = user.role
        
        # 检查是否为教师
        if role != 'teacher':
            return {'message': '需要教师权限'}, 403
        
        return f(*args, **kwargs)
    
    return decorated_function


def student_required(f):
    """
    装饰器：要求用户必须是学生角色
    必须在 @jwt_required() 之后使用
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取当前用户ID（转换为整数）
        current_user_id_str = get_jwt_identity()
        if not current_user_id_str:
            return {'message': '未认证'}, 401
        
        current_user_id = int(current_user_id_str)
        
        # 从JWT中获取角色信息（如果存在）
        jwt_data = get_jwt()
        role = jwt_data.get('role')
        
        # 如果JWT中没有角色信息，从数据库查询
        if not role:
            user = User.query.get(current_user_id)
            if not user:
                return {'message': '用户不存在'}, 404
            role = user.role
        
        # 检查是否为学生
        if role != 'student':
            return {'message': '需要学生权限'}, 403
        
        return f(*args, **kwargs)
    
    return decorated_function

