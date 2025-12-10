from flask import request, send_file, jsonify
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc, and_, or_
import pandas as pd
import numpy as np
from io import BytesIO
import json
from datetime import datetime, timedelta, timezone
import random
import string
from models import db
from models.user import User, StudentClass
from models.class_model import Class, ChatRoom
from models.course import Course, CourseMaterial, Assignment, CourseClass, CourseTeacher
from models.exam import Exam, ExamResult, QuestionBank, MCQQuestion, StudentAnswer, ExamClass
from models.notification import Notification
from models.score import Score
from models.question import Question, Answer, Reply, ChatMessage
from utils.decorators import teacher_required
from utils.excel_handler import ExcelHandler
from services.score_service import ScoreService
from services.analysis_service import AnalysisService


class TeacherStudents(Resource):
    @jwt_required()
    @teacher_required
    def get(self):
        """获取所有学生列表（用于添加到班级）"""
        # 获取查询参数
        search = request.args.get('search', '')
        exclude_class_id = request.args.get('exclude_class_id', type=int)
        
        # 构建查询
        query = User.query.filter_by(role='student', is_active=True)
        
        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    User.name.like(f'%{search}%'),
                    User.username.like(f'%{search}%'),
                    User.email.like(f'%{search}%')
                )
            )
        
        # 排除已在指定班级的学生
        if exclude_class_id:
            students_in_class = db.session.query(StudentClass.student_id).filter_by(
                class_id=exclude_class_id
            ).subquery()
            query = query.filter(~User.id.in_(students_in_class))
        
        students = query.limit(100).all()
        
        return {
            'message': '获取成功',
            'data': [student.to_dict() for student in students]
        }, 200


class TeacherClasses(Resource):
    @jwt_required()
    @teacher_required
    def get(self):
        """获取教师的所有班级"""
        teacher_id = int(get_jwt_identity())

        classes = Class.query.filter_by(teacher_id=teacher_id).all()

        return {
            'message': '获取成功',
            'data': [cls.to_dict() for cls in classes],
            'total': len(classes)
        }, 200

    @jwt_required()
    @teacher_required
    def post(self):
        """创建新班级"""
        teacher_id = int(get_jwt_identity())
        data = request.get_json()

        # 验证输入
        if not data.get('name'):
            return {'message': '班级名称不能为空'}, 400

        # 生成班级代码
        code = self._generate_class_code()

        # 创建班级
        new_class = Class(
            name=data['name'],
            code=code,
            description=data.get('description', ''),
            teacher_id=teacher_id,
            course_id=data.get('course_id'),
            max_students=data.get('max_students', 100)
        )

        db.session.add(new_class)
        db.session.commit()

        # 创建聊天室
        chat_room = ChatRoom(class_id=new_class.id, name=f"{new_class.name}聊天室")
        db.session.add(chat_room)
        db.session.commit()

        return {
            'message': '班级创建成功',
            'data': new_class.to_dict()
        }, 201

    def _generate_class_code(self):
        """生成唯一的班级代码"""
        import random
        import string

        while True:
            code = 'CLS' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            if not Class.query.filter_by(code=code).first():
                return code


class TeacherClassDetail(Resource):
    @jwt_required()
    @teacher_required
    def get(self, class_id):
        """获取班级详情"""
        teacher_id = int(get_jwt_identity())

        class_ = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()

        if not class_:
            return {'message': '班级不存在或无权限访问'}, 404

        # 获取班级学生
        students = User.query.join(StudentClass).filter(
            StudentClass.class_id == class_id,
            User.role == 'student'
        ).all()

        # 获取班级统计信息
        exam_count = Exam.query.filter_by(class_id=class_id).count()
        score_count = Score.query.filter_by(class_id=class_id).count()
        question_count = Question.query.filter_by(class_id=class_id).count()

        class_data = class_.to_dict()
        class_data.update({
            'students': [student.to_dict() for student in students],
            'student_count': len(students),
            'exam_count': exam_count,
            'score_count': score_count,
            'question_count': question_count
        })

        return {
            'message': '获取成功',
            'data': class_data
        }, 200

    @jwt_required()
    @teacher_required
    def put(self, class_id):
        """更新班级信息"""
        teacher_id = int(get_jwt_identity())

        class_ = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()

        if not class_:
            return {'message': '班级不存在或无权限访问'}, 404

        data = request.get_json()

        if data.get('name'):
            class_.name = data['name']
        if data.get('description') is not None:
            class_.description = data['description']
        if data.get('course_id') is not None:
            class_.course_id = data['course_id']
        if data.get('max_students'):
            class_.max_students = data['max_students']
        if data.get('is_active') is not None:
            class_.is_active = data['is_active']

        db.session.commit()

        return {
            'message': '班级更新成功',
            'data': class_.to_dict()
        }, 200
    
    @jwt_required()
    @teacher_required
    def post(self, class_id):
        """添加学生到班级"""
        teacher_id = int(get_jwt_identity())
        
        class_ = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()
        
        if not class_:
            return {'message': '班级不存在或无权限访问'}, 404
        
        data = request.get_json()
        student_ids = data.get('student_ids', [])
        
        if not student_ids or not isinstance(student_ids, list):
            return {'message': '请提供学生ID列表'}, 400
        
        added_students = []
        errors = []
        
        for student_id in student_ids:
            try:
                # 检查学生是否存在
                student = User.query.filter_by(id=student_id, role='student').first()
                if not student:
                    errors.append(f'学生ID {student_id} 不存在或不是学生')
                    continue
                
                # 检查是否已经在班级中
                existing = StudentClass.query.filter_by(
                    class_id=class_id,
                    student_id=student_id
                ).first()
                
                if existing:
                    errors.append(f'学生 {student.name} 已在班级中')
                    continue
                
                # 检查班级人数限制
                current_count = StudentClass.query.filter_by(class_id=class_id).count()
                if class_.max_students and current_count >= class_.max_students:
                    errors.append(f'班级人数已达上限 ({class_.max_students}人)')
                    break
                
                # 添加学生到班级
                student_class = StudentClass(
                    class_id=class_id,
                    student_id=student_id
                )
                db.session.add(student_class)
                added_students.append({
                    'id': student.id,
                    'name': student.name,
                    'username': student.username
                })
            except Exception as e:
                errors.append(f'添加学生 {student_id} 失败: {str(e)}')
        
        db.session.commit()
        
        return {
            'message': f'成功添加 {len(added_students)} 名学生',
            'data': {
                'added': added_students,
                'errors': errors
            }
        }, 200
    
    @jwt_required()
    @teacher_required
    def delete(self, class_id):
        """删除班级"""
        teacher_id = int(get_jwt_identity())
        
        class_ = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()
        
        if not class_:
            return {'message': '班级不存在或无权限访问'}, 404
        
        # 检查是否有学生
        student_count = StudentClass.query.filter_by(class_id=class_id).count()
        if student_count > 0:
            return {'message': '班级中还有学生，无法删除'}, 400
        
        db.session.delete(class_)
        db.session.commit()
        
        return {'message': '班级删除成功'}, 200

    @jwt_required()
    @teacher_required
    def delete(self, class_id):
        """删除班级"""
        teacher_id = int(get_jwt_identity())

        class_ = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()

        if not class_:
            return {'message': '班级不存在或无权限访问'}, 404

        # 检查是否有依赖数据
        exam_count = Exam.query.filter_by(class_id=class_id).count()
        score_count = Score.query.filter_by(class_id=class_id).count()

        if exam_count > 0 or score_count > 0:
            return {
                'message': '班级存在关联数据，无法删除',
                'exam_count': exam_count,
                'score_count': score_count
            }, 400

        db.session.delete(class_)
        db.session.commit()

        return {'message': '班级删除成功'}, 200


class TeacherExams(Resource):
    @jwt_required()
    @teacher_required
    def get(self):
        """获取教师的所有考试"""
        teacher_id = int(get_jwt_identity())

        # 获取查询参数
        class_id = request.args.get('class_id')
        status = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # 构建查询
        query = Exam.query.filter_by(teacher_id=teacher_id)

        if class_id:
            query = query.filter_by(class_id=class_id)

        if status:
            query = query.filter_by(status=status)

        # 分页
        exams = query.order_by(desc(Exam.created_at)) \
            .paginate(page=page, per_page=per_page, error_out=False)

        # 获取考试统计信息
        exam_list = []
        for exam in exams.items:
            exam_data = exam.to_dict()
            # 获取参与人数
            participant_count = ExamResult.query.filter_by(exam_id=exam.id).count()
            exam_data['participant_count'] = participant_count
            exam_list.append(exam_data)

        return {
            'message': '获取成功',
            'data': exam_list,
            'pagination': {
                'page': exams.page,
                'per_page': exams.per_page,
                'total': exams.total,
                'pages': exams.pages
            }
        }, 200

    @jwt_required()
    @teacher_required
    def post(self):
        """创建新考试"""
        teacher_id = int(get_jwt_identity())
        data = request.get_json()

        # 验证输入（class_id 改为可选，发布时再选择）
        required_fields = ['title', 'start_time', 'end_time', 'duration']
        for field in required_fields:
            if not data.get(field):
                return {'message': f'{field}不能为空'}, 400

        # 如果提供了 class_id，验证班级是否存在且属于该教师
        class_id = data.get('class_id')
        if class_id:
            class_ = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()
            if not class_:
                return {'message': '班级不存在或无权限访问'}, 400

        # 如果选择了题库，从题库中随机选择题目
        question_bank_id = data.get('question_bank_id')
        total_questions = data.get('total_questions', 0)
        
        if question_bank_id and total_questions > 0:
            # 验证题库是否存在且属于该教师
            question_bank = QuestionBank.query.filter_by(
                id=question_bank_id,
                teacher_id=teacher_id
            ).first()
            
            if not question_bank:
                return {'message': '题库不存在或无权限访问'}, 400
            
            # 检查题库中的题目数量
            available_questions = MCQQuestion.query.filter_by(
                question_bank_id=question_bank_id
            ).count()
            
            if available_questions < total_questions:
                return {
                    'message': f'题库中只有{available_questions}道题目，无法选择{total_questions}道题目'
                }, 400
        
        # 创建考试（class_id 可选，发布时再选择）
        exam = Exam(
            title=data['title'],
            description=data.get('description', ''),
            class_id=class_id,  # 可以为 None
            teacher_id=teacher_id,
            question_bank_id=question_bank_id,
            total_questions=total_questions,
            total_score=data.get('total_score', 100.0),
            passing_score=data.get('passing_score', 60.0),
            start_time=datetime.fromisoformat(data['start_time']),
            end_time=datetime.fromisoformat(data['end_time']),
            duration=data['duration'],
            auto_grade=data.get('auto_grade', True)
        )

        db.session.add(exam)
        db.session.commit()

        return {
            'message': '考试创建成功',
            'data': exam.to_dict()
        }, 201


class TeacherScores(Resource):
    @jwt_required()
    @teacher_required
    def get(self):
        """获取成绩列表"""
        teacher_id = int(get_jwt_identity())

        # 获取查询参数
        class_id = request.args.get('class_id')
        exam_id = request.args.get('exam_id')
        student_name = request.args.get('student_name')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))

        # 构建查询 - 只获取该教师班级的成绩
        query = Score.query.join(Class).filter(
            Class.teacher_id == teacher_id
        )

        if class_id:
            query = query.filter(Score.class_id == class_id)

        if exam_id:
            query = query.filter(Score.exam_id == exam_id)

        if student_name:
            query = query.join(User, Score.student_id == User.id) \
                .filter(User.name.ilike(f'%{student_name}%'))

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
            except ValueError:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Score.recorded_at >= start_dt)

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
            except ValueError:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            # 包含整天：加一天再减一秒
            end_dt = end_dt + timedelta(days=1) - timedelta(seconds=1)
            query = query.filter(Score.recorded_at <= end_dt)

        # 分页
        scores = query.order_by(desc(Score.recorded_at)) \
            .paginate(page=page, per_page=per_page, error_out=False)

        # 获取详细数据
        score_list = []
        for score in scores.items:
            score_data = score.to_dict()
            # 获取学生信息
            student = User.query.get(score.student_id)
            if student:
                score_data['student_name'] = student.name
                score_data['student_id'] = student.username
            # 获取班级信息
            class_ = Class.query.get(score.class_id)
            if class_:
                score_data['class_name'] = class_.name
            # 获取考试信息
            if score.exam_id:
                exam = Exam.query.get(score.exam_id)
                if exam:
                    score_data['exam_title'] = exam.title
            score_list.append(score_data)

        # 获取统计信息
        stats = ScoreService.get_score_statistics(teacher_id, class_id, exam_id, start_date, end_date)

        return {
            'message': '获取成功',
            'data': score_list,
            'statistics': stats,
            'pagination': {
                'page': scores.page,
                'per_page': scores.per_page,
                'total': scores.total,
                'pages': scores.pages
            }
        }, 200

    @jwt_required()
    @teacher_required
    def post(self):
        """手动录入成绩"""
        teacher_id = int(get_jwt_identity())
        data = request.get_json()

        # 验证输入
        if not data.get('scores') or not isinstance(data['scores'], list):
            return {'message': '成绩数据格式错误'}, 400

        created_scores = []
        errors = []

        for score_data in data['scores']:
            try:
                # 验证必填字段
                required_fields = ['student_id', 'class_id', 'subject', 'score', 'total_score']
                for field in required_fields:
                    if not score_data.get(field):
                        errors.append(f"成绩记录缺少必填字段: {field}")
                        continue

                # 检查班级是否属于该教师
                class_ = Class.query.filter_by(
                    id=score_data['class_id'],
                    teacher_id=teacher_id
                ).first()

                if not class_:
                    errors.append(f"班级不存在或无权限访问: {score_data['class_id']}")
                    continue

                # 创建成绩记录
                score = Score(
                    student_id=score_data['student_id'],
                    class_id=score_data['class_id'],
                    exam_id=score_data.get('exam_id'),
                    subject=score_data['subject'],
                    score=score_data['score'],
                    total_score=score_data['total_score'],
                    type='manual',
                    recorded_by=teacher_id,
                    comments=score_data.get('comments'),
                    recorded_at=datetime.now(timezone.utc)
                )

                db.session.add(score)
                created_scores.append(score)

            except Exception as e:
                errors.append(str(e))

        if errors and not created_scores:
            return {'message': '录入失败', 'errors': errors}, 400

        db.session.commit()

        return {
            'message': '成绩录入成功',
            'data': [score.to_dict() for score in created_scores],
            'errors': errors if errors else None
        }, 201


class TeacherScoreDetail(Resource):
    @jwt_required()
    @teacher_required
    def get(self, score_id):
        """获取成绩详情"""
        teacher_id = int(get_jwt_identity())

        score = Score.query.join(Class).filter(
            Score.id == score_id,
            Class.teacher_id == teacher_id
        ).first()

        if not score:
            return {'message': '成绩不存在或无权限访问'}, 404

        score_data = score.to_dict()
        # 补充相关信息
        student = User.query.get(score.student_id)
        if student:
            score_data['student_name'] = student.name
            score_data['student_info'] = student.to_dict()

        class_ = Class.query.get(score.class_id)
        if class_:
            score_data['class_name'] = class_.name

        if score.exam_id:
            exam = Exam.query.get(score.exam_id)
            if exam:
                score_data['exam_title'] = exam.title

        return {
            'message': '获取成功',
            'data': score_data
        }, 200

    @jwt_required()
    @teacher_required
    def put(self, score_id):
        """更新成绩"""
        teacher_id = int(get_jwt_identity())

        score = Score.query.join(Class).filter(
            Score.id == score_id,
            Class.teacher_id == teacher_id
        ).first()

        if not score:
            return {'message': '成绩不存在或无权限访问'}, 404

        data = request.get_json()

        if data.get('score') is not None:
            score.score = data['score']
        if data.get('total_score') is not None:
            score.total_score = data['total_score']
        if data.get('comments') is not None:
            score.comments = data['comments']

        db.session.commit()

        return {
            'message': '成绩更新成功',
            'data': score.to_dict()
        }, 200

    @jwt_required()
    @teacher_required
    def delete(self, score_id):
        """删除成绩"""
        teacher_id = int(get_jwt_identity())

        score = Score.query.join(Class).filter(
            Score.id == score_id,
            Class.teacher_id == teacher_id
        ).first()

        if not score:
            return {'message': '成绩不存在或无权限访问'}, 404

        db.session.delete(score)
        db.session.commit()

        return {'message': '成绩删除成功'}, 200


class ScoreImportExport(Resource):
    @jwt_required()
    @teacher_required
    def post(self):
        """导入Excel成绩"""
        teacher_id = int(get_jwt_identity())

        if 'file' not in request.files:
            return {'message': '没有上传文件'}, 400

        file = request.files['file']

        if not file.filename:
            return {'message': '文件名为空'}, 400

        # 检查文件格式
        if not file.filename.endswith(('.xlsx', '.xls')):
            return {'message': '只支持Excel文件格式'}, 400

        try:
            # 使用ExcelHandler处理文件
            result = ExcelHandler.import_scores_from_excel(file, teacher_id)

            if result['errors']:
                return {
                    'message': '部分数据导入成功',
                    'success_count': result['success_count'],
                    'errors': result['errors']
                }, 207  # Multi-Status

            return {
                'message': '成绩导入成功',
                'success_count': result['success_count']
            }, 200

        except Exception as e:
            return {'message': f'导入失败: {str(e)}'}, 500

    @jwt_required()
    @teacher_required
    def get(self):
        """导出Excel成绩"""
        teacher_id = int(get_jwt_identity())

        # 获取查询参数
        class_id = request.args.get('class_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 获取成绩数据
        scores = ScoreService.get_scores_for_export(teacher_id, class_id, start_date, end_date)

        # 生成Excel文件
        excel_file = ExcelHandler.export_scores_to_excel(scores)

        # 创建文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'成绩导出_{timestamp}.xlsx'

        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )


class ScoreAnalysis(Resource):
    @jwt_required()
    @teacher_required
    def get(self):
        """成绩分析"""
        teacher_id = int(get_jwt_identity())

        # 获取查询参数
        class_id = request.args.get('class_id')
        exam_id = request.args.get('exam_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # 获取分析结果
        analysis = AnalysisService.analyze_scores(teacher_id, class_id, exam_id, start_date, end_date)

        return {
            'message': '分析成功',
            'data': analysis
        }, 200


class ScorePrediction(Resource):
    @jwt_required()
    @teacher_required
    def post(self):
        """成绩预测"""
        teacher_id = int(get_jwt_identity())
        data = request.get_json()

        if not data.get('student_id') or not data.get('class_id'):
            return {'message': '学生ID和班级ID不能为空'}, 400

        # 获取历史成绩
        history_scores = Score.query.filter_by(
            student_id=data['student_id'],
            class_id=data['class_id']
        ).order_by(Score.recorded_at).all()

        if len(history_scores) < 3:
            return {'message': '历史数据不足，无法进行预测'}, 400

        # 使用机器学习模型进行预测
        try:
            from ml_models.score_predictor import ScorePredictor

            predictor = ScorePredictor()
            prediction = predictor.predict_next_score(history_scores)

            return {
                'message': '预测成功',
                'data': {
                    'predicted_score': prediction['score'],
                    'confidence': prediction['confidence'],
                    'trend': prediction['trend']
                }
            }, 200

        except Exception as e:
            return {'message': f'预测失败: {str(e)}'}, 500


class TeacherExamDetail(Resource):
    @jwt_required()
    @teacher_required
    def get(self, exam_id):
        """获取考试详情"""
        teacher_id = int(get_jwt_identity())
        
        exam = Exam.query.filter_by(id=exam_id, teacher_id=teacher_id).first()
        
        if not exam:
            return {'message': '考试不存在或无权限访问'}, 404
        
        exam_data = exam.to_dict()
        # 获取参与人数和统计信息
        participant_count = ExamResult.query.filter_by(exam_id=exam_id).count()
        exam_data['participant_count'] = participant_count
        
        return {
            'message': '获取成功',
            'data': exam_data
        }, 200
    
    @jwt_required()
    @teacher_required
    def put(self, exam_id):
        """更新考试信息"""
        teacher_id = int(get_jwt_identity())
        
        exam = Exam.query.filter_by(id=exam_id, teacher_id=teacher_id).first()
        
        if not exam:
            return {'message': '考试不存在或无权限访问'}, 404
        
        data = request.get_json()
        
        if data.get('title'):
            exam.title = data['title']
        if data.get('description') is not None:
            exam.description = data['description']
        if data.get('start_time'):
            exam.start_time = datetime.fromisoformat(data['start_time'])
        if data.get('end_time'):
            exam.end_time = datetime.fromisoformat(data['end_time'])
        if data.get('duration'):
            exam.duration = data['duration']
        if data.get('total_score'):
            exam.total_score = data['total_score']
        if data.get('passing_score'):
            exam.passing_score = data['passing_score']
        if data.get('status'):
            # 确保状态值是小写字符串，匹配数据库ENUM定义
            status_value = data['status'].lower() if isinstance(data['status'], str) else str(data['status']).lower()
            if status_value in ['draft', 'published', 'ongoing', 'ended']:
                exam.status = status_value
        
        if data.get('scheduled_publish_time'):
            exam.scheduled_publish_time = datetime.fromisoformat(data['scheduled_publish_time'])
        
        db.session.commit()
        
        return {
            'message': '考试更新成功',
            'data': exam.to_dict()
        }, 200
    
    @jwt_required()
    @teacher_required
    def delete(self, exam_id):
        """删除考试"""
        teacher_id = int(get_jwt_identity())
        
        exam = Exam.query.filter_by(id=exam_id, teacher_id=teacher_id).first()
        
        if not exam:
            return {'message': '考试不存在或无权限访问'}, 404
        
        # 检查是否有考试结果
        result_count = ExamResult.query.filter_by(exam_id=exam_id).count()
        if result_count > 0:
            return {'message': '考试已有结果记录，无法删除'}, 400
        
        db.session.delete(exam)
        db.session.commit()
        
        return {'message': '考试删除成功'}, 200


class TeacherExamPublish(Resource):
    @jwt_required()
    @teacher_required
    def post(self, exam_id):
        """发布考试（立即发布或定时发布）"""
        teacher_id = int(get_jwt_identity())
        
        exam = Exam.query.filter_by(id=exam_id, teacher_id=teacher_id).first()
        
        if not exam:
            return {'message': '考试不存在或无权限访问'}, 404
        
        data = request.get_json()
        publish_type = data.get('publish_type', 'immediate')  # immediate 或 scheduled
        scheduled_time = data.get('scheduled_publish_time')
        
        # 发布时必须选择班级列表
        class_ids = data.get('class_ids') or data.get('class_id')
        if not class_ids:
            return {'message': '发布考试时必须选择至少一个班级'}, 400
        if isinstance(class_ids, int):
            class_ids = [class_ids]
        if not isinstance(class_ids, list) or len(class_ids) == 0:
            return {'message': '发布考试时必须选择至少一个班级'}, 400
        
        # 验证班级是否存在且属于该教师
        valid_classes = Class.query.filter(
            Class.id.in_(class_ids),
            Class.teacher_id == teacher_id
        ).all()
        if len(valid_classes) != len(class_ids):
            return {'message': '存在无权限或不存在的班级'}, 400
        
        # 更新考试班级关联（覆盖）
        exam.exam_classes.clear()
        for cid in class_ids:
            exam.exam_classes.append(ExamClass(class_id=cid))
        # 保留主班级字段为首个（兼容旧字段）
        exam.class_id = class_ids[0]
        
        # 获取要发布的学生列表
        student_ids = data.get('student_ids', [])  # 如果为空，则发布给所选班级全部学生
        
        if publish_type == 'immediate':
            # 立即发布
            exam.status = 'published'
            exam.scheduled_publish_time = None
            
            # 发送通知给所有班级学生
            from models.user import StudentClass
            
            # 如果指定了学生ID，只通知这些学生；否则通知所选班级全部学生
            if student_ids:
                target_students = User.query.filter(
                    User.id.in_(student_ids),
                    User.role == 'student'
                ).all()
            else:
                # 获取所选班级所有学生并去重
                target_students = User.query.join(StudentClass).filter(
                    StudentClass.class_id.in_(class_ids),
                    User.role == 'student'
                ).distinct().all()
            
            # 创建通知
            notifications = []
            for student in target_students:
                notification = Notification(
                    user_id=student.id,
                    type='exam_published',
                    title=f'新考试通知：{exam.title}',
                    content=f'教师发布了新考试：{exam.title}。考试时间：{exam.start_time.strftime("%Y-%m-%d %H:%M")} 至 {exam.end_time.strftime("%Y-%m-%d %H:%M")}',
                    related_id=exam.id,
                    related_type='exam'
                )
                db.session.add(notification)
                notifications.append(notification)
            
            db.session.commit()
            
            return {
                'message': f'考试已发布，已通知 {len(notifications)} 名学生',
                'data': {
                    'exam_id': exam.id,
                    'status': 'published',
                    'notified_count': len(notifications)
                }
            }, 200
        
        elif publish_type == 'scheduled':
            # 定时发布
            if not scheduled_time:
                return {'message': '定时发布需要提供发布时间'}, 400
            
            scheduled_datetime = datetime.fromisoformat(scheduled_time)
            if scheduled_datetime <= datetime.now(timezone.utc):
                return {'message': '定时发布时间必须晚于当前时间'}, 400
            
            exam.status = 'draft'  # 保持草稿状态，等待定时发布
            exam.scheduled_publish_time = scheduled_datetime
            
            db.session.commit()
            
            return {
                'message': f'考试已设置为定时发布，将在 {scheduled_datetime.strftime("%Y-%m-%d %H:%M")} 自动发布',
                'data': {
                    'exam_id': exam.id,
                    'scheduled_publish_time': scheduled_datetime.isoformat()
                }
            }, 200
        
        else:
            return {'message': '发布类型无效，必须是 immediate 或 scheduled'}, 400


class TeacherCourses(Resource):
    @jwt_required()
    @teacher_required
    def get(self):
        """获取教师的所有课程"""
        teacher_id = int(get_jwt_identity())
        
        courses = Course.query \
            .join(CourseTeacher, CourseTeacher.course_id == Course.id, isouter=True) \
            .filter((Course.teacher_id == teacher_id) | (CourseTeacher.teacher_id == teacher_id)) \
            .distinct() \
            .all()
        
        return {
            'message': '获取成功',
            'data': [course.to_dict() for course in courses],
            'total': len(courses)
        }, 200
    
    @jwt_required()
    @teacher_required
    def post(self):
        """创建新课程"""
        teacher_id = int(get_jwt_identity())
        data = request.get_json()
        # 验证输入
        required_fields = ['name', 'semester']
        for field in required_fields:
            if not data.get(field):
                return {'message': f'{field}不能为空'}, 400

        # 课程代码：若未提供或为空，自动生成
        code = (data.get('code') or '').strip()
        if not code:
            code = self._generate_course_code()
        else:
            # 检查课程代码是否已存在
            if Course.query.filter_by(code=code).first():
                return {'message': '课程代码已存在'}, 400
        
        # 创建课程
        course = Course(
            name=data['name'],
            code=code,
            description=data.get('description', ''),
            teacher_id=teacher_id,
            semester=data['semester'],
            credit=data.get('credit', 3.0),
            hours_per_week=data.get('hours_per_week', 3),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(course)
        db.session.commit()

        # 记录教师-课程关系（多对多）
        if not CourseTeacher.query.filter_by(course_id=course.id, teacher_id=teacher_id).first():
            db.session.add(CourseTeacher(course_id=course.id, teacher_id=teacher_id))
            db.session.commit()

        # 绑定班级（可选，多对多）
        class_ids = data.get('classes') or []
        if class_ids:
            teacher_class_ids = {c.id for c in Class.query.filter_by(teacher_id=teacher_id).all()}
            valid_ids = [cid for cid in class_ids if cid in teacher_class_ids]
            for cid in valid_ids:
                db.session.add(CourseClass(course_id=course.id, class_id=cid))
            db.session.commit()
        
        return {
            'message': '课程创建成功',
            'data': course.to_dict()
        }, 201

    def _generate_course_code(self):
        """生成唯一课程代码"""
        prefix = 'C'
        for _ in range(10):
            suffix = ''.join(random.choices(string.digits + string.ascii_uppercase, k=5))
            code = f"{prefix}{suffix}"
            if not Course.query.filter_by(code=code).first():
                return code
        # 退化处理
        return f"{prefix}{int(datetime.now().timestamp())}"


class TeacherCourseDetail(Resource):
    @jwt_required()
    @teacher_required
    def get(self, course_id):
        """获取课程详情"""
        teacher_id = int(get_jwt_identity())
        
        course = Course.query \
            .join(CourseTeacher, CourseTeacher.course_id == Course.id, isouter=True) \
            .filter((Course.teacher_id == teacher_id) | (CourseTeacher.teacher_id == teacher_id)) \
            .filter(Course.id == course_id) \
            .first()
        
        if not course:
            return {'message': '课程不存在或无权限访问'}, 404
        
        course_data = course.to_dict()
        # 获取关联的班级（多对多）
        classes = Class.query.join(CourseClass, CourseClass.class_id == Class.id) \
            .filter(CourseClass.course_id == course_id).all()
        course_data['classes'] = [cls.to_dict() for cls in classes]
        
        return {
            'message': '获取成功',
            'data': course_data
        }, 200

    @jwt_required()
    @teacher_required
    def delete(self, course_id):
        """删除课程（解绑班级后删除）"""
        teacher_id = int(get_jwt_identity())
        
        course = Course.query \
            .join(CourseTeacher, CourseTeacher.course_id == Course.id, isouter=True) \
            .filter((Course.teacher_id == teacher_id) | (CourseTeacher.teacher_id == teacher_id)) \
            .filter(Course.id == course_id) \
            .first()
        if not course:
            return {'message': '课程不存在或无权限访问'}, 404

        # 解绑班级关联
        CourseClass.query.filter_by(course_id=course.id).delete()

        db.session.delete(course)
        db.session.commit()

        return {'message': '课程已删除'}, 200

class TeacherCourseClasses(Resource):
    @jwt_required()
    @teacher_required
    def post(self, course_id):
        """绑定/更新课程的班级列表"""
        teacher_id = int(get_jwt_identity())
        data = request.get_json() or {}
        class_ids = data.get('class_ids') or data.get('classes') or []

        course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()
        if not course:
            return {'message': '课程不存在或无权限访问'}, 404

        # 仅允许绑定自己的班级
        teacher_classes = Class.query.filter_by(teacher_id=teacher_id).all()
        teacher_class_ids = {c.id for c in teacher_classes}
        valid_ids = [cid for cid in class_ids if cid in teacher_class_ids]

        # 清除原绑定（多对多）并清空 classes.course_id 以保持一致
        CourseClass.query.filter_by(course_id=course.id).delete()
        Class.query.filter_by(course_id=course.id, teacher_id=teacher_id).update({'course_id': None}, synchronize_session=False)
        # 绑定新的（如有）
        for cid in valid_ids:
            db.session.add(CourseClass(course_id=course.id, class_id=cid))
            Class.query.filter_by(id=cid, teacher_id=teacher_id).update({'course_id': course.id}, synchronize_session=False)

        db.session.commit()

        # 返回最新课程信息
        course_data = course.to_dict()
        classes = Class.query.join(CourseClass, CourseClass.class_id == Class.id) \
            .filter(CourseClass.course_id == course.id).all()
        course_data['classes'] = [cls.to_dict() for cls in classes]

        return {
            'message': '班级绑定已更新',
            'data': course_data
        }, 200
    
    @jwt_required()
    @teacher_required
    def put(self, course_id):
        """更新课程信息"""
        teacher_id = int(get_jwt_identity())
        
        course = Course.query.filter_by(id=course_id, teacher_id=teacher_id).first()
        
        if not course:
            return {'message': '课程不存在或无权限访问'}, 404
        
        data = request.get_json()
        
        if data.get('name'):
            course.name = data['name']
        if data.get('description') is not None:
            course.description = data['description']
        if data.get('semester'):
            course.semester = data['semester']
        if data.get('credit'):
            course.credit = data['credit']
        if data.get('hours_per_week'):
            course.hours_per_week = data['hours_per_week']
        if data.get('is_active') is not None:
            course.is_active = data['is_active']

        # 绑定班级（可选，覆盖，多对多）
        if 'classes' in data:
            class_ids = data.get('classes') or []
            teacher_class_ids = {c.id for c in Class.query.filter_by(teacher_id=teacher_id).all()}
            valid_ids = [cid for cid in class_ids if cid in teacher_class_ids]
            # 清空原关联
            CourseClass.query.filter_by(course_id=course.id).delete()
            # 写入新关联
            for cid in valid_ids:
                db.session.add(CourseClass(course_id=course.id, class_id=cid))
        
        db.session.commit()
        
        return {
            'message': '课程更新成功',
            'data': course.to_dict()
        }, 200
    
class TeacherQuestions(Resource):
    @jwt_required()
    @teacher_required
    def get(self):
        """获取教师的所有提问"""
        teacher_id = int(get_jwt_identity())
        
        # 获取查询参数
        class_id = request.args.get('class_id')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # 构建查询
        query = Question.query.filter_by(teacher_id=teacher_id)
        
        if class_id:
            query = query.filter_by(class_id=class_id)
        
        # 分页
        questions = query.order_by(desc(Question.created_at)) \
            .paginate(page=page, per_page=per_page, error_out=False)
        
        question_list = []
        for question in questions.items:
            question_data = question.to_dict()
            # 获取回答数量
            answer_count = Answer.query.filter_by(question_id=question.id).count()
            question_data['answer_count'] = answer_count
            question_list.append(question_data)
        
        return {
            'message': '获取成功',
            'data': question_list,
            'pagination': {
                'page': questions.page,
                'per_page': questions.per_page,
                'total': questions.total,
                'pages': questions.pages
            }
        }, 200
    
    @jwt_required()
    @teacher_required
    def post(self):
        """创建新提问"""
        teacher_id = int(get_jwt_identity())
        data = request.get_json()
        
        # 验证输入
        required_fields = ['class_id', 'content']
        for field in required_fields:
            if not data.get(field):
                return {'message': f'{field}不能为空'}, 400
        
        # 检查班级是否属于该教师
        class_ = Class.query.filter_by(id=data['class_id'], teacher_id=teacher_id).first()
        if not class_:
            return {'message': '班级不存在或无权限访问'}, 400
        
        # 创建提问
        question = Question(
            class_id=data['class_id'],
            teacher_id=teacher_id,
            content=data['content'],
            type=data.get('type', 'individual'),
            random_count=data.get('random_count'),
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
            is_active=data.get('is_active', True)
        )
        
        db.session.add(question)
        db.session.commit()
        
        return {
            'message': '提问创建成功',
            'data': question.to_dict()
        }, 201


class TeacherQuestionDetail(Resource):
    @jwt_required()
    @teacher_required
    def get(self, question_id):
        """获取提问详情"""
        teacher_id = int(get_jwt_identity())
        
        question = Question.query.filter_by(id=question_id, teacher_id=teacher_id).first()
        
        if not question:
            return {'message': '提问不存在或无权限访问'}, 404
        
        question_data = question.to_dict()
        # 获取所有回答
        answers = Answer.query.filter_by(question_id=question_id).all()
        question_data['answers'] = [answer.to_dict() for answer in answers]
        
        return {
            'message': '获取成功',
            'data': question_data
        }, 200
    
    @jwt_required()
    @teacher_required
    def put(self, question_id):
        """更新提问"""
        teacher_id = int(get_jwt_identity())
        
        question = Question.query.filter_by(id=question_id, teacher_id=teacher_id).first()
        
        if not question:
            return {'message': '提问不存在或无权限访问'}, 404
        
        data = request.get_json()
        
        if data.get('content'):
            question.content = data['content']
        if data.get('due_date'):
            question.due_date = datetime.fromisoformat(data['due_date'])
        if data.get('is_active') is not None:
            question.is_active = data['is_active']
        
        db.session.commit()
        
        return {
            'message': '提问更新成功',
            'data': question.to_dict()
        }, 200
    
    @jwt_required()
    @teacher_required
    def delete(self, question_id):
        """删除提问"""
        teacher_id = int(get_jwt_identity())
        
        question = Question.query.filter_by(id=question_id, teacher_id=teacher_id).first()
        
        if not question:
            return {'message': '提问不存在或无权限访问'}, 404
        
        # 检查是否有回答
        answer_count = Answer.query.filter_by(question_id=question_id).count()
        if answer_count > 0:
            return {'message': '提问已有回答，无法删除'}, 400
        
        db.session.delete(question)
        db.session.commit()
        
        return {'message': '提问删除成功'}, 200


# 题库管理
class TeacherQuestionBanks(Resource):
    @jwt_required()
    @teacher_required
    def get(self):
        """获取教师的所有题库"""
        teacher_id = int(get_jwt_identity())
        
        question_banks = QuestionBank.query.filter_by(teacher_id=teacher_id).all()
        
        result = []
        for bank in question_banks:
            bank_data = {
                'id': bank.id,
                'name': bank.name,
                'description': bank.description,
                'is_public': bank.is_public,
                'question_count': bank.question_count,
                'created_at': bank.created_at.isoformat() if bank.created_at else None,
                'updated_at': bank.updated_at.isoformat() if bank.updated_at else None
            }
            result.append(bank_data)
        
        return {
            'message': '获取成功',
            'data': result
        }, 200
    
    @jwt_required()
    @teacher_required
    def post(self):
        """创建新题库"""
        teacher_id = int(get_jwt_identity())
        data = request.get_json()
        
        if not data.get('name'):
            return {'message': '题库名称不能为空'}, 400
        
        question_bank = QuestionBank(
            name=data['name'],
            description=data.get('description', ''),
            teacher_id=teacher_id,
            is_public=data.get('is_public', False)
        )
        
        db.session.add(question_bank)
        db.session.commit()
        
        return {
            'message': '题库创建成功',
            'data': {
                'id': question_bank.id,
                'name': question_bank.name,
                'description': question_bank.description,
                'is_public': question_bank.is_public,
                'question_count': 0,
                'created_at': question_bank.created_at.isoformat() if question_bank.created_at else None
            }
        }, 201


class TeacherQuestionBankDetail(Resource):
    @jwt_required()
    @teacher_required
    def get(self, bank_id):
        """获取题库详情（包含题目列表）"""
        teacher_id = int(get_jwt_identity())
        
        question_bank = QuestionBank.query.filter_by(id=bank_id, teacher_id=teacher_id).first()
        
        if not question_bank:
            return {'message': '题库不存在或无权限访问'}, 404
        
        questions = MCQQuestion.query.filter_by(question_bank_id=bank_id).all()
        
        return {
            'message': '获取成功',
            'data': {
                'id': question_bank.id,
                'name': question_bank.name,
                'description': question_bank.description,
                'is_public': question_bank.is_public,
                'question_count': question_bank.question_count,
                'questions': [q.to_dict() for q in questions],
                'created_at': question_bank.created_at.isoformat() if question_bank.created_at else None,
                'updated_at': question_bank.updated_at.isoformat() if question_bank.updated_at else None
            }
        }, 200
    
    @jwt_required()
    @teacher_required
    def put(self, bank_id):
        """更新题库信息"""
        teacher_id = int(get_jwt_identity())
        
        question_bank = QuestionBank.query.filter_by(id=bank_id, teacher_id=teacher_id).first()
        
        if not question_bank:
            return {'message': '题库不存在或无权限访问'}, 404
        
        data = request.get_json()
        
        if data.get('name'):
            question_bank.name = data['name']
        if data.get('description') is not None:
            question_bank.description = data['description']
        if data.get('is_public') is not None:
            question_bank.is_public = data['is_public']
        
        question_bank.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        
        return {
            'message': '题库更新成功',
            'data': {
                'id': question_bank.id,
                'name': question_bank.name,
                'description': question_bank.description,
                'is_public': question_bank.is_public,
                'question_count': question_bank.question_count
            }
        }, 200
    
    @jwt_required()
    @teacher_required
    def delete(self, bank_id):
        """删除题库"""
        teacher_id = int(get_jwt_identity())
        
        question_bank = QuestionBank.query.filter_by(id=bank_id, teacher_id=teacher_id).first()
        
        if not question_bank:
            return {'message': '题库不存在或无权限访问'}, 404
        
        # 检查是否有题目
        question_count = MCQQuestion.query.filter_by(question_bank_id=bank_id).count()
        if question_count > 0:
            return {'message': '题库中有题目，无法删除'}, 400
        
        db.session.delete(question_bank)
        db.session.commit()
        
        return {'message': '题库删除成功'}, 200


class TeacherMCQQuestions(Resource):
    @jwt_required()
    @teacher_required
    def post(self):
        """添加选择题到题库"""
        teacher_id = int(get_jwt_identity())
        data = request.get_json()
        
        # 验证输入
        required_fields = ['question_bank_id', 'content', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option']
        for field in required_fields:
            if not data.get(field):
                return {'message': f'{field}不能为空'}, 400
        
        # 验证题库是否存在且属于该教师
        question_bank = QuestionBank.query.filter_by(
            id=data['question_bank_id'],
            teacher_id=teacher_id
        ).first()
        
        if not question_bank:
            return {'message': '题库不存在或无权限访问'}, 404
        
        # 验证正确答案选项
        if data['correct_option'] not in ['A', 'B', 'C', 'D']:
            return {'message': '正确答案必须是A、B、C或D'}, 400
        
        # 创建题目
        question = MCQQuestion(
            question_bank_id=data['question_bank_id'],
            content=data['content'],
            option_a=data['option_a'],
            option_b=data['option_b'],
            option_c=data['option_c'],
            option_d=data['option_d'],
            correct_option=data['correct_option'].upper(),
            explanation=data.get('explanation', ''),
            score=data.get('score', 1.0),
            difficulty=data.get('difficulty', 'medium')
        )
        
        db.session.add(question)
        db.session.commit()
        
        return {
            'message': '题目添加成功',
            'data': question.to_dict()
        }, 201


class TeacherMCQQuestionDetail(Resource):
    @jwt_required()
    @teacher_required
    def put(self, question_id):
        """更新选择题"""
        teacher_id = int(get_jwt_identity())
        
        question = MCQQuestion.query.get(question_id)
        
        if not question:
            return {'message': '题目不存在'}, 404
        
        # 验证题库是否属于该教师
        question_bank = QuestionBank.query.filter_by(
            id=question.question_bank_id,
            teacher_id=teacher_id
        ).first()
        
        if not question_bank:
            return {'message': '无权限访问'}, 403
        
        data = request.get_json()
        
        if data.get('content'):
            question.content = data['content']
        if data.get('option_a'):
            question.option_a = data['option_a']
        if data.get('option_b'):
            question.option_b = data['option_b']
        if data.get('option_c'):
            question.option_c = data['option_c']
        if data.get('option_d'):
            question.option_d = data['option_d']
        if data.get('correct_option'):
            if data['correct_option'] not in ['A', 'B', 'C', 'D']:
                return {'message': '正确答案必须是A、B、C或D'}, 400
            question.correct_option = data['correct_option'].upper()
        if data.get('explanation') is not None:
            question.explanation = data['explanation']
        if data.get('score'):
            question.score = data['score']
        if data.get('difficulty'):
            question.difficulty = data['difficulty']
        
        db.session.commit()
        
        return {
            'message': '题目更新成功',
            'data': question.to_dict()
        }, 200
    
    @jwt_required()
    @teacher_required
    def delete(self, question_id):
        """删除选择题"""
        teacher_id = int(get_jwt_identity())
        
        question = MCQQuestion.query.get(question_id)
        
        if not question:
            return {'message': '题目不存在'}, 404
        
        # 验证题库是否属于该教师
        question_bank = QuestionBank.query.filter_by(
            id=question.question_bank_id,
            teacher_id=teacher_id
        ).first()
        
        if not question_bank:
            return {'message': '无权限访问'}, 403
        
        db.session.delete(question)
        db.session.commit()
        
        return {'message': '题目删除成功'}, 200