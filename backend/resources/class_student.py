"""
班级学生管理相关API
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db
from models.user import User, StudentClass
from models.class_model import Class
from utils.decorators import teacher_required


class ClassStudent(Resource):
    @jwt_required()
    @teacher_required
    def delete(self, class_id, student_id):
        """从班级中移除学生"""
        teacher_id = int(get_jwt_identity())
        
        # 验证班级是否属于该教师
        class_ = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()
        
        if not class_:
            return {'message': '班级不存在或无权限访问'}, 404
        
        # 查找学生班级关联
        student_class = StudentClass.query.filter_by(
            class_id=class_id,
            student_id=student_id
        ).first()
        
        if not student_class:
            return {'message': '学生不在该班级中'}, 404
        
        # 获取学生信息用于返回
        student = User.query.get(student_id)
        student_name = student.name if student else f'ID: {student_id}'
        
        # 删除关联
        db.session.delete(student_class)
        db.session.commit()
        
        return {
            'message': f'学生 {student_name} 已从班级中移除',
            'data': {
                'student_id': student_id,
                'class_id': class_id
            }
        }, 200

