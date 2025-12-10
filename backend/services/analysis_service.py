"""
成绩分析服务
"""
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import joblib
import os
import sys

# 添加项目路径，确保可以导入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class AnalysisService:
    @staticmethod
    def analyze_scores(teacher_id, class_id=None, exam_id=None, start_date=None, end_date=None):
        """成绩分析服务"""
        try:
            # 动态导入模型，避免循环导入
            from models.score import Score
            from models.class_model import Class
            from models import db

            # 获取成绩数据
            query = db.session.query(Score).join(Class).filter(Class.teacher_id == teacher_id)

            if class_id:
                query = query.filter(Score.class_id == class_id)

            if exam_id:
                query = query.filter(Score.exam_id == exam_id)

            if start_date:
                query = query.filter(Score.recorded_at >= start_date)

            if end_date:
                query = query.filter(Score.recorded_at <= end_date)

            scores = query.all()

            if not scores:
                return {
                    'basic_statistics': {},
                    'distribution': {},
                    'trend_analysis': [],
                    'cluster_analysis': {},
                    'correlation_analysis': {}
                }

            # 转换为DataFrame
            scores_data = []
            for score in scores:
                # 计算百分比（如果数据库中没有存储）
                percentage = score.percentage
                if percentage is None and score.total_score > 0:
                    percentage = (score.score / score.total_score) * 100

                scores_data.append({
                    'student_id': score.student_id,
                    'class_id': score.class_id,
                    'score': score.score,
                    'total_score': score.total_score,
                    'percentage': percentage or 0,
                    'subject': score.subject,
                    'recorded_at': score.recorded_at
                })

            df = pd.DataFrame(scores_data)

            if df.empty:
                return {
                    'basic_statistics': {},
                    'distribution': {},
                    'trend_analysis': [],
                    'cluster_analysis': {},
                    'correlation_analysis': {}
                }

            # 基础统计分析
            basic_stats = {}
            if 'percentage' in df.columns and not df['percentage'].empty:
                basic_stats = {
                    'count': len(df),
                    'mean': round(df['percentage'].mean(), 2),
                    'std': round(df['percentage'].std(), 2),
                    'min': round(df['percentage'].min(), 2),
                    '25%': round(df['percentage'].quantile(0.25), 2),
                    '50%': round(df['percentage'].median(), 2),
                    '75%': round(df['percentage'].quantile(0.75), 2),
                    'max': round(df['percentage'].max(), 2)
                }

            # 分数分布
            distribution = {}
            if 'percentage' in df.columns and not df['percentage'].empty:
                bins = [0, 60, 70, 80, 90, 100]
                labels = ['不及格', '及格', '中等', '良好', '优秀']

                try:
                    df['grade'] = pd.cut(df['percentage'], bins=bins, labels=labels, include_lowest=True)
                    distribution = df['grade'].value_counts().to_dict()
                except Exception as e:
                    print(f"分数分布计算错误: {e}")
                    distribution = {}

            # 趋势分析（按时间）
            trend_data = []
            if 'recorded_at' in df.columns and len(df) > 1:
                try:
                    df['date'] = pd.to_datetime(df['recorded_at']).dt.date
                    trend = df.groupby('date')['percentage'].mean().reset_index()
                    trend_data = [
                        {'date': str(row['date']), 'average_percentage': round(row['percentage'], 2)}
                        for _, row in trend.iterrows()
                    ]
                except Exception as e:
                    print(f"趋势分析错误: {e}")
                    trend_data = []

            # 聚类分析
            cluster_results = AnalysisService._cluster_students(df)

            # 相关性分析
            correlation = AnalysisService._analyze_correlations(df)

            return {
                'basic_statistics': basic_stats,
                'distribution': distribution,
                'trend_analysis': trend_data,
                'cluster_analysis': cluster_results,
                'correlation_analysis': correlation
            }

        except ImportError as e:
            print(f"导入错误: {e}")
            return {
                'basic_statistics': {},
                'distribution': {},
                'trend_analysis': [],
                'cluster_analysis': {'error': f'模型导入失败: {str(e)}'},
                'correlation_analysis': {}
            }

    @staticmethod
    def _cluster_students(df, n_clusters=3):
        """对学生进行聚类分析"""
        if len(df) < n_clusters or 'percentage' not in df.columns:
            return {'error': '数据量不足以进行聚类分析'}

        try:
            # 准备特征
            features = df[['percentage']].values

            # 标准化
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(features)

            # KMeans聚类
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(features_scaled)

            df['cluster'] = clusters

            # 分析每个簇的特征
            cluster_analysis = {}
            for cluster_id in range(n_clusters):
                cluster_data = df[df['cluster'] == cluster_id]
                cluster_analysis[f'cluster_{cluster_id}'] = {
                    'count': len(cluster_data),
                    'average_percentage': round(cluster_data['percentage'].mean(), 2) if not cluster_data.empty else 0,
                    'min_percentage': round(cluster_data['percentage'].min(), 2) if not cluster_data.empty else 0,
                    'max_percentage': round(cluster_data['percentage'].max(), 2) if not cluster_data.empty else 0,
                    'student_ids': cluster_data['student_id'].tolist()[
                                   :10] if 'student_id' in cluster_data.columns else []
                }

            return cluster_analysis

        except Exception as e:
            return {'error': f'聚类分析失败: {str(e)}'}

    @staticmethod
    def _analyze_correlations(df):
        """分析相关性"""
        if len(df) < 2:
            return {}

        # 如果有多个科目，分析科目之间的相关性
        if 'subject' in df.columns and len(df['subject'].unique()) > 1:
            try:
                # 创建科目成绩透视表
                subject_pivot = df.pivot_table(
                    values='percentage',
                    index='student_id',
                    columns='subject',
                    aggfunc='mean'
                ).dropna()

                if len(subject_pivot) > 1:
                    correlation_matrix = subject_pivot.corr()

                    # 转换为易读的格式
                    correlations = []
                    for i, col1 in enumerate(correlation_matrix.columns):
                        for j, col2 in enumerate(correlation_matrix.columns):
                            if i < j:  # 只取上三角矩阵
                                correlations.append({
                                    'subject1': col1,
                                    'subject2': col2,
                                    'correlation': round(correlation_matrix.iloc[i, j], 3)
                                })

                    # 按相关性绝对值排序
                    correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)

                    strongest_positive = max(correlations, key=lambda x: x['correlation']) if correlations else {}
                    strongest_negative = min(correlations, key=lambda x: x['correlation']) if correlations else {}

                    return {
                        'subject_correlations': correlations[:10],  # 只返回前10个
                        'strongest_positive': strongest_positive,
                        'strongest_negative': strongest_negative
                    }
            except Exception as e:
                print(f"相关性分析错误: {e}")
                return {}

        return {}

    @staticmethod
    def predict_final_scores(class_id, features_df):
        """预测学生期末成绩"""
        try:
            # 获取配置
            from config import Config

            # 加载或训练模型
            model_path = os.path.join(Config.MODEL_PATH, f'class_{class_id}_model.pkl')

            if os.path.exists(model_path):
                model = joblib.load(model_path)
            else:
                # 如果没有预训练模型，使用线性回归
                model = LinearRegression()
                # 这里需要历史数据进行训练
                # 在实际应用中，你需要收集足够的历史数据来训练模型
                return {'error': '没有足够的训练数据'}

            # 进行预测
            predictions = model.predict(features_df)

            return {
                'predictions': predictions.tolist(),
                'model_type': type(model).__name__,
                'confidence': 0.8  # 示例置信度
            }

        except ImportError:
            return {'error': '配置导入失败'}
        except Exception as e:
            return {'error': f'预测失败: {str(e)}'}

    @staticmethod
    def identify_at_risk_students(class_id, threshold=60):
        """识别风险学生（成绩低于阈值）"""
        try:
            # 动态导入
            from models import db
            from models.user import User
            from models.score import Score

            # 获取班级所有学生的最新成绩
            latest_scores = db.session.query(
                User.id,
                User.name,
                Score.percentage,
                Score.subject,
                Score.recorded_at
            ).join(Score, User.id == Score.student_id) \
                .filter(Score.class_id == class_id) \
                .order_by(Score.recorded_at.desc()) \
                .all()

            # 去重，获取每个学生的最新成绩
            seen_students = set()
            at_risk_students = []

            for student in latest_scores:
                if student.id in seen_students:
                    continue
                seen_students.add(student.id)

                # 检查百分比是否存在
                percentage = student.percentage
                if percentage is None:
                    # 如果需要，可以从其他数据计算百分比
                    continue

                if percentage < threshold:
                    at_risk_students.append({
                        'student_id': student.id,
                        'student_name': student.name,
                        'latest_score': percentage,
                        'subject': student.subject,
                        'recorded_at': student.recorded_at.strftime('%Y-%m-%d') if student.recorded_at else ''
                    })

            return {
                'at_risk_count': len(at_risk_students),
                'threshold': threshold,
                'students': at_risk_students
            }

        except ImportError as e:
            return {'error': f'模型导入失败: {str(e)}'}
        except Exception as e:
            return {'error': f'识别风险学生失败: {str(e)}'}