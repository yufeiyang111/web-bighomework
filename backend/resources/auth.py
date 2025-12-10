from flask import request, jsonify
from flask_restful import Resource
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timezone
from models import db
from models.user import User
from utils.decorators import teacher_required
from utils.validators import validate_email, validate_password


class Login(Resource):
    def post(self):
        data = request.get_json()

        # 验证输入
        if not data or not data.get('username') or not data.get('password'):
            return {'message': '用户名和密码不能为空'}, 400

        user = User.query.filter_by(username=data['username']).first()

        if not user:
            return {'message': '用户名或密码错误'}, 401
        
        # 检查密码哈希是否存在
        if not user.password_hash:
            return {'message': '用户密码未设置，请联系管理员'}, 401
        
        # 检查密码
        try:
            if not user.check_password(data['password']):
                return {'message': '用户名或密码错误'}, 401
        except ValueError as e:
            # 如果密码哈希格式错误，尝试重新设置密码（仅用于修复）
            app.logger.error(f'密码哈希格式错误: {e}')
            return {'message': '用户密码格式错误，请联系管理员重置'}, 401

        if not user.is_active:
            return {'message': '账号已被禁用'}, 403

        # 创建JWT令牌（identity必须是字符串）
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role, 'username': user.username}
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        return {
            'message': '登录成功',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }, 200


class Register(Resource):
    def post(self):
        data = request.get_json()

        # 验证必填字段
        required_fields = ['username', 'email', 'password', 'name', 'role']
        for field in required_fields:
            if not data.get(field):
                return {'message': f'{field}不能为空'}, 400

        # 验证邮箱格式
        if not validate_email(data['email']):
            return {'message': '邮箱格式不正确'}, 400

        # 验证密码强度
        password_error = validate_password(data['password'])
        if password_error:
            return {'message': password_error}, 400

        # 检查用户名和邮箱是否已存在
        if User.query.filter_by(username=data['username']).first():
            return {'message': '用户名已存在'}, 400

        if User.query.filter_by(email=data['email']).first():
            return {'message': '邮箱已注册'}, 400

        # 创建用户
        user = User(
            username=data['username'],
            email=data['email'],
            name=data['name'],
            role=data['role'],
            department=data.get('department'),
            phone=data.get('phone')
        )
        user.set_password(data['password'])

        db.session.add(user)
        db.session.commit()

        return {
            'message': '注册成功',
            'user': user.to_dict()
        }, 201


class RefreshToken(Resource):
    @jwt_required(refresh=True)
    def post(self):
        current_user = get_jwt_identity()
        user = User.query.get(int(current_user))

        if not user or not user.is_active:
            return {'message': '用户不存在或已被禁用'}, 401

        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role, 'username': user.username}
        )

        return {
            'message': '令牌刷新成功',
            'access_token': access_token
        }, 200


class Logout(Resource):
    @jwt_required()
    def post(self):
        # 在实际项目中，可以将令牌加入黑名单
        return {'message': '登出成功'}, 200