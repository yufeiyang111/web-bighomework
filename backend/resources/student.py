"""
学生相关API资源
"""
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, desc, text
from datetime import datetime, timezone
from models import db
from models.user import User, StudentClass
from models.class_model import Class
from models.exam import Exam, ExamResult, QuestionBank, MCQQuestion, StudentAnswer
from models.score import Score
from utils.decorators import student_required


class StudentExams(Resource):
    @jwt_required()
    @student_required
    def get(self):
        """获取学生可参加的考试列表"""
        student_id = int(get_jwt_identity())
        
        # 获取学生所在的班级
        student_classes = StudentClass.query.filter_by(student_id=student_id).all()
        class_ids = [sc.class_id for sc in student_classes]
        
        if not class_ids:
            return {
                'message': '获取成功',
                'data': []
            }, 200
        
        # 获取这些班级的考试
        exams = Exam.query.filter(Exam.class_id.in_(class_ids)).all()
        
        result = []
        for exam in exams:
            # 检查学生是否已经参加过考试
            exam_result = ExamResult.query.filter_by(
                exam_id=exam.id,
                student_id=student_id
            ).first()
            
            exam_data = exam.to_dict()
            exam_data['has_taken'] = exam_result is not None
            exam_data['score'] = exam_result.score if exam_result else None
            exam_data['submitted_at'] = exam_result.submitted_at.isoformat() if exam_result and exam_result.submitted_at else None
            
            result.append(exam_data)
        
        return {
            'message': '获取成功',
            'data': result
        }, 200


class StudentExamDetail(Resource):
    @jwt_required()
    @student_required
    def get(self, exam_id):
        """获取考试详情和题目（开始考试）"""
        student_id = int(get_jwt_identity())
        
        exam = Exam.query.get(exam_id)
        
        if not exam:
            return {'message': '考试不存在'}, 404
        
        # 检查学生是否有权限参加这个考试
        student_class = StudentClass.query.filter_by(
            student_id=student_id,
            class_id=exam.class_id
        ).first()
        
        if not student_class:
            return {'message': '您没有权限参加此考试'}, 403
        
        # 检查考试时间
        now = datetime.now(timezone.utc)
        if now < exam.start_time:
            return {'message': '考试尚未开始'}, 400
        if now > exam.end_time:
            return {'message': '考试已结束'}, 400
        
        # 检查是否已经参加过考试
        exam_result = ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).first()
        
        if exam_result and exam_result.submitted_at:
            return {'message': '您已经提交过此考试'}, 400
        
        # 如果没有考试记录，创建新的考试记录
        if not exam_result:
            exam_result = ExamResult(
                exam_id=exam_id,
                student_id=student_id,
                total_score=exam.total_score,
                start_time=now
            )
            db.session.add(exam_result)
            db.session.commit()
        
        # 从题库中获取题目（如果考试有题库）
        questions = []
        if exam.question_bank_id and exam.total_questions > 0:
            # 检查是否已经为这个学生分配了题目
            existing_answers = StudentAnswer.query.filter_by(
                exam_result_id=exam_result.id
            ).all()
            
            if existing_answers:
                # 如果已经有答案记录，说明题目已经分配，返回已分配的题目
                question_ids = [answer.question_id for answer in existing_answers]
                questions = MCQQuestion.query.filter(
                    MCQQuestion.id.in_(question_ids)
                ).all()
            else:
                # 从题库中随机选择题目（MySQL使用RAND()）
                all_questions = MCQQuestion.query.filter_by(
                    question_bank_id=exam.question_bank_id
                ).order_by(text('RAND()')).limit(exam.total_questions).all()
                
                # 为每个题目创建答案记录
                for question in all_questions:
                    student_answer = StudentAnswer(
                        exam_result_id=exam_result.id,
                        question_id=question.id
                    )
                    db.session.add(student_answer)
                
                db.session.commit()
                questions = all_questions
        
        # 返回考试信息和题目（不包含正确答案）
        exam_data = exam.to_dict()
        exam_data['questions'] = [
            {
                'id': q.id,
                'content': q.content,
                'options': {
                    'A': q.option_a,
                    'B': q.option_b,
                    'C': q.option_c,
                    'D': q.option_d
                },
                'score': q.score
            }
            for q in questions
        ]
        exam_data['exam_result_id'] = exam_result.id
        exam_data['start_time'] = exam_result.start_time.isoformat() if exam_result.start_time else None
        
        return {
            'message': '获取成功',
            'data': exam_data
        }, 200


class StudentSubmitExam(Resource):
    @jwt_required()
    @student_required
    def post(self, exam_id):
        """提交考试答案"""
        student_id = int(get_jwt_identity())
        data = request.get_json()
        
        exam = Exam.query.get(exam_id)
        
        if not exam:
            return {'message': '考试不存在'}, 404
        
        # 检查学生是否有权限
        student_class = StudentClass.query.filter_by(
            student_id=student_id,
            class_id=exam.class_id
        ).first()
        
        if not student_class:
            return {'message': '您没有权限参加此考试'}, 403
        
        # 获取考试记录
        exam_result = ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).first()
        
        if not exam_result:
            return {'message': '请先开始考试'}, 400
        
        if exam_result.submitted_at:
            return {'message': '您已经提交过此考试'}, 400
        
        # 检查考试时间
        now = datetime.now(timezone.utc)
        if now > exam.end_time:
            return {'message': '考试已结束'}, 400
        
        # 获取答案数据
        answers = data.get('answers', {})  # {question_id: 'A'/'B'/'C'/'D'}
        
        # 保存答案并自动批改
        total_score = 0.0
        for question_id_str, selected_option in answers.items():
            try:
                question_id = int(question_id_str)
            except ValueError:
                continue
            
            # 获取题目
            question = MCQQuestion.query.get(question_id)
            if not question:
                continue
            
            # 获取或创建答案记录
            student_answer = StudentAnswer.query.filter_by(
                exam_result_id=exam_result.id,
                question_id=question_id
            ).first()
            
            if not student_answer:
                student_answer = StudentAnswer(
                    exam_result_id=exam_result.id,
                    question_id=question_id
                )
            
            # 保存学生选择的答案
            student_answer.selected_option = selected_option.upper() if selected_option else None
            
            # 自动批改
            if student_answer.selected_option == question.correct_option:
                student_answer.is_correct = True
                student_answer.score = question.score
                total_score += question.score
            else:
                student_answer.is_correct = False
                student_answer.score = 0.0
            
            student_answer.answered_at = now
            
            if not student_answer.id:
                db.session.add(student_answer)
        
        # 更新考试结果
        exam_result.score = total_score
        exam_result.total_score = exam.total_score
        exam_result.end_time = now
        exam_result.submitted_at = now
        exam_result.ip_address = request.remote_addr
        
        db.session.commit()
        
        # 如果启用了自动批改，自动录入成绩
        if exam.auto_grade:
            # 检查是否已经存在成绩记录
            existing_score = Score.query.filter_by(
                student_id=student_id,
                class_id=exam.class_id,
                exam_id=exam_id
            ).first()
            
            if not existing_score:
                # 创建成绩记录
                score = Score(
                    student_id=student_id,
                    class_id=exam.class_id,
                    exam_id=exam_id,
                    subject=exam.title,
                    score=total_score,
                    total_score=exam.total_score,
                    type='exam',
                    recorded_by=exam.teacher_id,
                    comments=f'自动批改：{exam.title}'
                )
                db.session.add(score)
                db.session.commit()
            else:
                # 更新已有成绩
                existing_score.score = total_score
                existing_score.total_score = exam.total_score
                existing_score.updated_at = now
                db.session.commit()
        
        return {
            'message': '提交成功',
            'data': {
                'score': total_score,
                'total_score': exam.total_score,
                'percentage': (total_score / exam.total_score * 100) if exam.total_score > 0 else 0,
                'passed': total_score >= exam.passing_score
            }
        }, 200


class StudentExamResult(Resource):
    @jwt_required()
    @student_required
    def get(self, exam_id):
        """获取考试结果和答案解析"""
        student_id = int(get_jwt_identity())
        
        exam = Exam.query.get(exam_id)
        
        if not exam:
            return {'message': '考试不存在'}, 404
        
        # 获取考试结果
        exam_result = ExamResult.query.filter_by(
            exam_id=exam_id,
            student_id=student_id
        ).first()
        
        if not exam_result:
            return {'message': '您还没有参加此考试'}, 404
        
        # 获取所有答案
        student_answers = StudentAnswer.query.filter_by(
            exam_result_id=exam_result.id
        ).all()
        
        # 构建结果数据
        answers_detail = []
        for student_answer in student_answers:
            question = student_answer.question
            answers_detail.append({
                'question_id': question.id,
                'content': question.content,
                'options': {
                    'A': question.option_a,
                    'B': question.option_b,
                    'C': question.option_c,
                    'D': question.option_d
                },
                'correct_option': question.correct_option,
                'selected_option': student_answer.selected_option,
                'is_correct': student_answer.is_correct,
                'score': student_answer.score,
                'explanation': question.explanation
            })
        
        return {
            'message': '获取成功',
            'data': {
                'exam': exam.to_dict(),
                'result': exam_result.to_dict(),
                'answers': answers_detail
            }
        }, 200

