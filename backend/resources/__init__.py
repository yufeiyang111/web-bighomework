from flask import Blueprint
from flask_restful import Api

api_bp = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_bp)

# 导入所有资源
from .auth import Login, Register, RefreshToken, Logout
from .teacher import (
    TeacherClasses, TeacherClassDetail,
    TeacherExams, TeacherExamDetail, TeacherExamPublish,
    TeacherScores, TeacherScoreDetail,
    TeacherCourses, TeacherCourseDetail,
    TeacherCourseClasses,
    TeacherQuestions, TeacherQuestionDetail,
    TeacherQuestionBanks, TeacherQuestionBankDetail,
    TeacherMCQQuestions, TeacherMCQQuestionDetail,
    TeacherStudents
)
from .class_student import ClassStudent
from .student import (
    StudentExams, StudentExamDetail,
    StudentSubmitExam, StudentExamResult
)

# 认证资源
api.add_resource(Login, '/auth/login')
api.add_resource(Register, '/auth/register')
api.add_resource(RefreshToken, '/auth/refresh')
api.add_resource(Logout, '/auth/logout')

# 教师资源
api.add_resource(TeacherClasses, '/teacher/classes')
api.add_resource(TeacherClassDetail, '/teacher/classes/<int:class_id>')
api.add_resource(ClassStudent, '/teacher/classes/<int:class_id>/students/<int:student_id>')
api.add_resource(TeacherStudents, '/teacher/students')
api.add_resource(TeacherExams, '/teacher/exams')
api.add_resource(TeacherExamDetail, '/teacher/exams/<int:exam_id>')
api.add_resource(TeacherExamPublish, '/teacher/exams/<int:exam_id>/publish')
api.add_resource(TeacherScores, '/teacher/scores')
api.add_resource(TeacherScoreDetail, '/teacher/scores/<int:score_id>')
api.add_resource(TeacherCourses, '/teacher/courses')
api.add_resource(TeacherCourseDetail, '/teacher/courses/<int:course_id>')
api.add_resource(TeacherCourseClasses, '/teacher/courses/<int:course_id>/classes')
api.add_resource(TeacherQuestions, '/teacher/questions')
api.add_resource(TeacherQuestionDetail, '/teacher/questions/<int:question_id>')
api.add_resource(TeacherQuestionBanks, '/teacher/question-banks')
api.add_resource(TeacherQuestionBankDetail, '/teacher/question-banks/<int:bank_id>')
api.add_resource(TeacherMCQQuestions, '/teacher/mcq-questions')
api.add_resource(TeacherMCQQuestionDetail, '/teacher/mcq-questions/<int:question_id>')

# 学生资源
api.add_resource(StudentExams, '/student/exams')
api.add_resource(StudentExamDetail, '/student/exams/<int:exam_id>')
api.add_resource(StudentSubmitExam, '/student/exams/<int:exam_id>/submit')
api.add_resource(StudentExamResult, '/student/exams/<int:exam_id>/result')