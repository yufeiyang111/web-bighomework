"""
Excel文件处理工具
"""
import pandas as pd
from io import BytesIO
from datetime import datetime, timezone
from models import db
from models.user import User
from models.class_model import Class
from models.score import Score
from models.exam import Exam


class ExcelHandler:
    """Excel文件处理类"""
    
    @staticmethod
    def import_scores_from_excel(file, teacher_id):
        """
        从Excel文件导入成绩
        
        Args:
            file: Flask上传的文件对象
            teacher_id: 教师ID
            
        Returns:
            dict: 包含success_count和errors的字典
        """
        errors = []
        success_count = 0
        
        try:
            # 读取Excel文件
            df = pd.read_excel(file)
            
            # 验证必需的列
            required_columns = ['student_id', 'class_id', 'subject', 'score', 'total_score']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                errors.append(f'缺少必需的列: {", ".join(missing_columns)}')
                return {'success_count': 0, 'errors': errors}
            
            # 处理每一行数据
            for index, row in df.iterrows():
                try:
                    # 获取数据
                    student_id = row.get('student_id')
                    class_id = row.get('class_id')
                    subject = row.get('subject')
                    score = row.get('score')
                    total_score = row.get('total_score')
                    exam_id = row.get('exam_id', None)
                    comments = row.get('comments', '')
                    
                    # 验证数据
                    if pd.isna(student_id) or pd.isna(class_id) or pd.isna(subject) or pd.isna(score) or pd.isna(total_score):
                        errors.append(f'第{index + 2}行: 必填字段不能为空')
                        continue
                    
                    # 验证班级是否属于该教师
                    class_ = Class.query.filter_by(
                        id=int(class_id),
                        teacher_id=teacher_id
                    ).first()
                    
                    if not class_:
                        errors.append(f'第{index + 2}行: 班级不存在或无权限访问 (class_id: {class_id})')
                        continue
                    
                    # 验证学生是否存在
                    student = User.query.filter_by(
                        id=int(student_id),
                        role='student'
                    ).first()
                    
                    if not student:
                        errors.append(f'第{index + 2}行: 学生不存在 (student_id: {student_id})')
                        continue
                    
                    # 验证考试是否存在（如果提供了exam_id）
                    if exam_id and not pd.isna(exam_id):
                        exam = Exam.query.filter_by(id=int(exam_id)).first()
                        if not exam:
                            errors.append(f'第{index + 2}行: 考试不存在 (exam_id: {exam_id})')
                            continue
                    
                    # 创建成绩记录
                    score_record = Score(
                        student_id=int(student_id),
                        class_id=int(class_id),
                        exam_id=int(exam_id) if exam_id and not pd.isna(exam_id) else None,
                        subject=str(subject),
                        score=float(score),
                        total_score=float(total_score),
                        type='imported',
                        recorded_by=teacher_id,
                        comments=str(comments) if comments else None,
                        recorded_at=datetime.now(timezone.utc)
                    )
                    
                    db.session.add(score_record)
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f'第{index + 2}行: {str(e)}')
                    continue
            
            # 提交所有更改
            if success_count > 0:
                db.session.commit()
            
        except Exception as e:
            errors.append(f'文件处理错误: {str(e)}')
            db.session.rollback()
        
        return {
            'success_count': success_count,
            'errors': errors
        }
    
    @staticmethod
    def export_scores_to_excel(scores):
        """
        导出成绩到Excel文件
        
        Args:
            scores: 成绩数据列表（通常是查询结果）
            
        Returns:
            BytesIO: Excel文件的字节流
        """
        try:
            # 将查询结果转换为DataFrame
            if not scores:
                # 如果没有数据，创建空DataFrame
                df = pd.DataFrame(columns=[
                    '学生姓名', '学号', '班级名称', '考试标题', 
                    '科目', '得分', '总分', '百分比', '类型', '备注', '记录时间'
                ])
            else:
                # 转换数据
                data = []
                for score in scores:
                    data.append({
                        '学生姓名': score.student_name if hasattr(score, 'student_name') else '',
                        '学号': score.student_id if hasattr(score, 'student_id') else '',
                        '班级名称': score.class_name if hasattr(score, 'class_name') else '',
                        '考试标题': score.exam_title if hasattr(score, 'exam_title') else '',
                        '科目': score.subject if hasattr(score, 'subject') else '',
                        '得分': score.score if hasattr(score, 'score') else '',
                        '总分': score.total_score if hasattr(score, 'total_score') else '',
                        '百分比': f"{score.percentage:.2f}%" if hasattr(score, 'percentage') and score.percentage else '',
                        '类型': score.type if hasattr(score, 'type') else '',
                        '备注': score.comments if hasattr(score, 'comments') else '',
                        '记录时间': score.recorded_at.strftime('%Y-%m-%d %H:%M:%S') if hasattr(score, 'recorded_at') and score.recorded_at else ''
                    })
                
                df = pd.DataFrame(data)
            
            # 创建Excel文件
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='成绩表')
                
                # 获取工作表并调整列宽
                worksheet = writer.sheets['成绩表']
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).map(len).max(),
                        len(str(col))
                    ) + 2
                    worksheet.column_dimensions[chr(65 + idx)].width = min(max_length, 50)
            
            output.seek(0)
            return output
            
        except Exception as e:
            # 如果出错，返回一个包含错误信息的空文件
            output = BytesIO()
            df = pd.DataFrame({'错误': [f'导出失败: {str(e)}']})
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)
            return output
    
    @staticmethod
    def validate_excel_format(file):
        """
        验证Excel文件格式
        
        Args:
            file: Flask上传的文件对象
            
        Returns:
            tuple: (is_valid, error_message)
        """
        try:
            # 检查文件扩展名
            if not file.filename.endswith(('.xlsx', '.xls')):
                return False, '只支持Excel文件格式 (.xlsx, .xls)'
            
            # 尝试读取文件
            df = pd.read_excel(file)
            
            # 检查必需的列
            required_columns = ['student_id', 'class_id', 'subject', 'score', 'total_score']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                return False, f'缺少必需的列: {", ".join(missing_columns)}'
            
            return True, None
            
        except Exception as e:
            return False, f'文件格式错误: {str(e)}'


