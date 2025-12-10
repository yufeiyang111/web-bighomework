from datetime import datetime, timedelta
from sqlalchemy import func, desc, and_, or_
import pandas as pd
import numpy as np
from models import db
from models.score import Score
from models.class_model import Class
from models.exam import Exam
from models.user import User


class ScoreService:
    @staticmethod
    def get_score_statistics(teacher_id, class_id=None, exam_id=None, start_date=None, end_date=None):
        """获取成绩统计信息"""
        # 构建查询
        query = Score.query.join(Class).filter(Class.teacher_id == teacher_id)

        if class_id:
            query = query.filter(Score.class_id == class_id)

        if exam_id:
            query = query.filter(Score.exam_id == exam_id)

        if start_date:
            query = query.filter(Score.recorded_at >= start_date)

        if end_date:
            query = query.filter(Score.recorded_at <= end_date)

        # 执行查询
        scores = query.all()

        if not scores:
            return {
                'average_score': 0,
                'highest_score': 0,
                'lowest_score': 0,
                'pass_rate': 0,
                'total_count': 0
            }

        # 转换为DataFrame进行统计分析
        scores_data = [{
            'score': score.score,
            'total_score': score.total_score,
            'percentage': score.percentage
        } for score in scores]

        df = pd.DataFrame(scores_data)

        # 计算统计指标
        average_score = df['score'].mean()
        highest_score = df['score'].max()
        lowest_score = df['score'].min()
        pass_count = len(df[df['percentage'] >= 60])
        pass_rate = (pass_count / len(df)) * 100 if len(df) > 0 else 0

        # 分数分布
        score_bins = [0, 60, 70, 80, 90, 100]
        score_labels = ['不及格', '及格', '中等', '良好', '优秀']

        if 'percentage' in df.columns:
            df['grade'] = pd.cut(df['percentage'], bins=score_bins, labels=score_labels, include_lowest=True)
            grade_distribution = df['grade'].value_counts().to_dict()
        else:
            grade_distribution = {}

        return {
            'average_score': round(average_score, 2),
            'highest_score': round(highest_score, 2),
            'lowest_score': round(lowest_score, 2),
            'pass_rate': round(pass_rate, 2),
            'total_count': len(df),
            'grade_distribution': grade_distribution,
            'score_range': {
                'min': int(df['score'].min()),
                'max': int(df['score'].max()),
                'q1': int(df['score'].quantile(0.25)),
                'median': int(df['score'].median()),
                'q3': int(df['score'].quantile(0.75))
            }
        }

    @staticmethod
    def get_scores_for_export(teacher_id, class_id=None, start_date=None, end_date=None):
        """获取导出用的成绩数据"""
        # 构建查询
        query = db.session.query(
            User.real_name.label('student_name'),
            User.system_account.label('student_id'),
            Class.name.label('class_name'),
            Exam.title.label('exam_title'),
            Score.subject,
            Score.score,
            Score.total_score,
            Score.percentage,
            Score.type,
            Score.comments,
            Score.recorded_at
        ).join(Class, Score.class_id == Class.id) \
            .join(User, Score.student_id == User.id) \
            .outerjoin(Exam, Score.exam_id == Exam.id) \
            .filter(Class.teacher_id == teacher_id)

        if class_id:
            query = query.filter(Score.class_id == class_id)

        if start_date:
            # 确保 start_date 是字符串时转换为 datetime
            if isinstance(start_date, str):
                from datetime import datetime
                try:
                    start_date = datetime.strptime(start_date, '%Y-%m-%d')
                except:
                    print(f'无法解析开始日期: {start_date}')
            query = query.filter(Score.recorded_at >= start_date)

        if end_date:
            # 确保 end_date 是字符串时转换为 datetime，并设置为当天的结束时间
            if isinstance(end_date, str):
                from datetime import datetime, timedelta
                try:
                    end_date = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
                except:
                    print(f'无法解析结束日期: {end_date}')
            query = query.filter(Score.recorded_at <= end_date)

        print(f'[ScoreService] 查询条件: class_id={class_id}, start_date={start_date}, end_date={end_date}')
        scores = query.order_by(Score.recorded_at.desc()).all()
        print(f'[ScoreService] 查询结果: {len(scores)} 条记录')

        # 转换为字典列表
        result = []
        for score in scores:
            result.append({
                '学生姓名': score.student_name,
                '学号': score.student_id,
                '班级': score.class_name,
                '考试名称': score.exam_title or '',
                '科目': score.subject,
                '成绩': score.score,
                '总分': score.total_score,
                '百分比': f'{score.percentage:.1f}%' if score.percentage else '',
                '录入方式': {
                    'exam': '考试录入',
                    'manual': '手动录入',
                    'imported': 'Excel导入'
                }.get(score.type, score.type),
                '备注': score.comments or '',
                '录入时间': score.recorded_at.strftime('%Y-%m-%d %H:%M:%S') if score.recorded_at else ''
            })

        return result

    @staticmethod
    def get_trend_analysis(teacher_id, class_id, period='month'):
        """获取成绩趋势分析"""
        from datetime import datetime, timedelta

        # 根据周期设置时间范围
        if period == 'week':
            days = 7
        elif period == 'month':
            days = 30
        elif period == 'semester':
            days = 180
        else:
            days = 30

        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # 查询成绩数据
        scores = Score.query.join(Class).filter(
            Class.teacher_id == teacher_id,
            Score.class_id == class_id,
            Score.recorded_at >= start_date,
            Score.recorded_at <= end_date
        ).order_by(Score.recorded_at).all()

        if not scores:
            return []

        # 按日期分组计算平均分
        import pandas as pd

        scores_data = [{
            'date': score.recorded_at.date(),
            'score': score.score,
            'percentage': score.percentage
        } for score in scores]

        df = pd.DataFrame(scores_data)
        df['date'] = pd.to_datetime(df['date'])

        # 按日期分组
        if period == 'week':
            grouped = df.groupby(df['date'].dt.date).agg({
                'score': 'mean',
                'percentage': 'mean'
            }).reset_index()
        else:
            grouped = df.groupby(pd.Grouper(key='date', freq='W')).agg({
                'score': 'mean',
                'percentage': 'mean'
            }).reset_index()
            grouped['date'] = grouped['date'].dt.date

        # 转换为字典列表
        trend_data = []
        for _, row in grouped.iterrows():
            trend_data.append({
                'date': str(row['date']),
                'average_score': round(row['score'], 2),
                'average_percentage': round(row['percentage'], 2)
            })

        return trend_data