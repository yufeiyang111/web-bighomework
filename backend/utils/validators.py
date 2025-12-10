"""
验证工具函数
"""
import re
from typing import Optional


def validate_email(email: str) -> bool:
    """
    验证邮箱格式
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 如果邮箱格式正确返回True，否则返回False
    """
    if not email:
        return False
    
    # 邮箱格式正则表达式
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password(password: str) -> Optional[str]:
    """
    验证密码强度
    
    Args:
        password: 密码字符串
        
    Returns:
        Optional[str]: 如果密码不符合要求返回错误信息，否则返回None
    """
    if not password:
        return '密码不能为空'
    
    if len(password) < 6:
        return '密码长度至少为6位'
    
    if len(password) > 128:
        return '密码长度不能超过128位'
    
    # 检查是否包含至少一个字母和一个数字
    has_letter = bool(re.search(r'[a-zA-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    
    if not (has_letter and has_digit):
        return '密码必须包含至少一个字母和一个数字'
    
    return None  # 密码符合要求


def validate_username(username: str) -> Optional[str]:
    """
    验证用户名格式
    
    Args:
        username: 用户名
        
    Returns:
        Optional[str]: 如果用户名不符合要求返回错误信息，否则返回None
    """
    if not username:
        return '用户名不能为空'
    
    if len(username) < 3:
        return '用户名长度至少为3位'
    
    if len(username) > 64:
        return '用户名长度不能超过64位'
    
    # 用户名只能包含字母、数字、下划线和连字符
    pattern = r'^[a-zA-Z0-9_-]+$'
    if not re.match(pattern, username):
        return '用户名只能包含字母、数字、下划线和连字符'
    
    return None  # 用户名符合要求


def validate_phone(phone: str) -> bool:
    """
    验证手机号格式（中国手机号）
    
    Args:
        phone: 手机号
        
    Returns:
        bool: 如果手机号格式正确返回True，否则返回False
    """
    if not phone:
        return False
    
    # 中国手机号格式：11位数字，以1开头
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))


