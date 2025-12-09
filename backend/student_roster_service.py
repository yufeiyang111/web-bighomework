"""
Student Roster Service
学生花名册管理服务
"""
import os
import json
import hashlib
from datetime import datetime
from werkzeug.utils import secure_filename
from database import Database
from PIL import Image
import base64
import io

class StudentRosterService:
    """学生花名册服务类"""
    
    UPLOAD_FOLDER = 'uploads/roster_faces'
    VERIFICATION_FOLDER = 'uploads/verification_faces'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    
    @staticmethod
    def init_folders():
        """初始化上传文件夹"""
        os.makedirs(StudentRosterService.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(StudentRosterService.VERIFICATION_FOLDER, exist_ok=True)
    
    @staticmethod
    def allowed_file(filename):
        """检查文件扩展名"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in StudentRosterService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def add_student_to_roster(teacher_id, student_data, face_image):
        """
        添加学生到花名册
        
        Args:
            teacher_id: 教师ID
            student_data: 学生基本信息字典
            face_image: 人脸图片文件对象
        
        Returns:
            dict: 包含roster_id的结果
        """
        try:
            # 验证文件
            if not face_image or not StudentRosterService.allowed_file(face_image.filename):
                return {'success': False, 'message': '无效的图片文件'}
            
            # 检查学号是否已存在
            check_sql = "SELECT roster_id FROM student_roster WHERE student_id_number = %s"
            existing = Database.execute_query(check_sql, (student_data['student_id_number'],), fetch_one=True)
            if existing:
                return {'success': False, 'message': '该学号已存在于花名册中'}
            
            # 保存图片
            StudentRosterService.init_folders()
            filename = secure_filename(f"{student_data['student_id_number']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
            filepath = os.path.join(StudentRosterService.UPLOAD_FOLDER, filename)
            
            # 压缩并保存图片
            img = Image.open(face_image)
            img.thumbnail((800, 800))  # 压缩到最大800x800
            img.save(filepath, 'JPEG', quality=85)
            
            # 生成简单的图片特征编码（使用图片哈希）
            face_encoding = StudentRosterService.generate_simple_encoding(filepath)
            
            # 插入数据库
            sql = """
                INSERT INTO student_roster 
                (student_name, student_id_number, gender, class_name, grade, 
                 contact_phone, face_image_path, face_encoding, uploaded_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (
                student_data['student_name'],
                student_data['student_id_number'],
                student_data.get('gender'),
                student_data.get('class_name'),
                student_data.get('grade'),
                student_data.get('contact_phone'),
                filepath,
                json.dumps(face_encoding),
                teacher_id
            )
            
            roster_id = Database.execute_query(sql, params, commit=True)
            
            return {
                'success': True,
                'roster_id': roster_id,
                'message': '学生信息添加成功'
            }
            
        except Exception as e:
            return {'success': False, 'message': f'添加失败: {str(e)}'}
    
    @staticmethod
    def generate_simple_encoding(image_path):
        """
        生成简单的图片特征编码
        使用感知哈希(pHash)算法
        """
        try:
            img = Image.open(image_path)
            img = img.convert('L')  # 转灰度
            img = img.resize((32, 32), Image.Resampling.LANCZOS)
            
            # 计算平均值
            pixels = list(img.getdata())
            avg = sum(pixels) / len(pixels)
            
            # 生成哈希
            hash_str = ''.join('1' if p > avg else '0' for p in pixels)
            
            return {'hash': hash_str, 'size': img.size}
        except Exception as e:
            return {'hash': '', 'error': str(e)}
    
    @staticmethod
    def get_teacher_roster(teacher_id, page=1, page_size=20):
        """获取教师上传的学生花名册"""
        try:
            offset = (page - 1) * page_size
            
            sql = """
                SELECT roster_id, student_name, student_id_number, gender, 
                       class_name, grade, contact_phone, is_registered,
                       created_at, updated_at
                FROM student_roster
                WHERE uploaded_by = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            students = Database.execute_query(sql, (teacher_id, page_size, offset), fetch_all=True)
            
            # 获取总数
            count_sql = "SELECT COUNT(*) as total FROM student_roster WHERE uploaded_by = %s"
            total = Database.execute_query(count_sql, (teacher_id,), fetch_one=True)
            
            # 转换时间格式
            for student in students:
                if 'created_at' in student and hasattr(student['created_at'], 'strftime'):
                    student['created_at'] = student['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                if 'updated_at' in student and hasattr(student['updated_at'], 'strftime'):
                    student['updated_at'] = student['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'success': True,
                'students': students,
                'total': total['total'],
                'page': page,
                'page_size': page_size
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def delete_student_from_roster(roster_id, teacher_id):
        """删除花名册中的学生"""
        try:
            # 验证权限
            check_sql = "SELECT uploaded_by, face_image_path FROM student_roster WHERE roster_id = %s"
            student = Database.execute_query(check_sql, (roster_id,), fetch_one=True)
            
            if not student:
                return {'success': False, 'message': '学生信息不存在'}
            
            if student['uploaded_by'] != teacher_id:
                return {'success': False, 'message': '无权删除此学生信息'}
            
            # 删除图片文件
            if student['face_image_path'] and os.path.exists(student['face_image_path']):
                os.remove(student['face_image_path'])
            
            # 删除数据库记录
            delete_sql = "DELETE FROM student_roster WHERE roster_id = %s"
            Database.execute_query(delete_sql, (roster_id,), commit=True)
            
            return {'success': True, 'message': '删除成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def verify_student_face(student_id_number, verification_image):
        """
        验证学生人脸
        
        Args:
            student_id_number: 学号
            verification_image: 验证图片文件对象
        
        Returns:
            dict: 验证结果，包含相似度分数
        """
        try:
            print("\n" + "="*80)
            print(f"[人脸验证] 开始验证 - 学号: {student_id_number}")
            
            # 查找学生记录
            sql = "SELECT roster_id, face_image_path, face_encoding, is_registered FROM student_roster WHERE student_id_number = %s"
            student = Database.execute_query(sql, (student_id_number,), fetch_one=True)
            
            if not student:
                print(f"[人脸验证] 失败: 学号不存在")
                print("="*80)
                return {'success': False, 'message': '该学号不在花名册中，请联系教师添加'}
            
            print(f"[人脸验证] 找到学生记录 - roster_id: {student['roster_id']}")
            print(f"[人脸验证] 原始图片路径: {student['face_image_path']}")
            print(f"[人脸验证] 是否已注册: {student['is_registered']}")
            
            if student['is_registered']:
                print(f"[人脸验证] 失败: 学生已注册")
                print("="*80)
                return {'success': False, 'message': '该学号已注册账号'}
            
            # 保存验证图片
            StudentRosterService.init_folders()
            filename = secure_filename(f"verify_{student_id_number}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
            filepath = os.path.join(StudentRosterService.VERIFICATION_FOLDER, filename)
            
            print(f"[人脸验证] 保存验证图片到: {filepath}")
            
            img = Image.open(verification_image)
            original_size = img.size
            img.thumbnail((800, 800))
            img.save(filepath, 'JPEG', quality=85)
            
            print(f"[人脸验证] 图片大小: 原始={original_size}, 压缩后={img.size}")
            
            # 生成验证图片编码
            print(f"[人脸验证] 生成验证图片编码...")
            verify_encoding = StudentRosterService.generate_simple_encoding(filepath)
            print(f"[人脸验证] 验证编码长度: {len(verify_encoding.get('hash', ''))}")
            
            stored_encoding = json.loads(student['face_encoding'])
            print(f"[人脸验证] 存储编码长度: {len(stored_encoding.get('hash', ''))}")
            
            # 计算相似度
            print(f"[人脸验证] 计算相似度...")
            similarity = StudentRosterService.calculate_similarity(stored_encoding, verify_encoding)
            print(f"[人脸验证] 相似度: {similarity:.4f} ({similarity*100:.2f}%)")
            print(f"[人脸验证] 阈值: 0.8000 (80.00%)")
            
            # 记录验证日志
            log_sql = """
                INSERT INTO student_verification_logs 
                (roster_id, verification_image_path, similarity_score, verification_status)
                VALUES (%s, %s, %s, %s)
            """
            status = 'success' if similarity >= 0.8 else 'failed'
            Database.execute_query(log_sql, (student['roster_id'], filepath, similarity, status), commit=True)
            print(f"[人脸验证] 日志已记录 - 状态: {status}")
            
            if similarity >= 0.8:  # 80%相似度阈值
                print(f"[人脸验证] ✅ 验证成功!")
                print("="*80 + "\n")
                return {
                    'success': True,
                    'roster_id': student['roster_id'],
                    'similarity': similarity,
                    'message': '人脸验证成功'
                }
            else:
                print(f"[人脸验证] ❌ 验证失败 - 相似度过低")
                print(f"[人脸验证] 需要: {0.8:.4f} ({80:.2f}%), 实际: {similarity:.4f} ({similarity*100:.2f}%)")
                print(f"[人脸验证] 差距: {(0.8 - similarity)*100:.2f}%")
                print("="*80 + "\n")
                return {
                    'success': False,
                    'similarity': similarity,
                    'message': f'人脸验证失败，相似度过低({similarity*100:.1f}%)，需要至少 80.0%'
                }
            
        except Exception as e:
            print(f"[人脸验证] 异常: {str(e)}")
            import traceback
            traceback.print_exc()
            print("="*80 + "\n")
            return {'success': False, 'message': f'验证失败: {str(e)}'}
    
    @staticmethod
    def calculate_similarity(encoding1, encoding2):
        """计算两个编码的相似度（基于汉明距离）"""
        try:
            hash1 = encoding1.get('hash', '')
            hash2 = encoding2.get('hash', '')
            
            if not hash1 or not hash2 or len(hash1) != len(hash2):
                return 0.0
            
            # 计算汉明距离
            distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
            # 转换为相似度 (0-1)
            similarity = 1 - (distance / len(hash1))
            
            return similarity
        except:
            return 0.0
    
    @staticmethod
    def mark_as_registered(roster_id, user_id):
        """标记学生已注册"""
        sql = """
            UPDATE student_roster 
            SET is_registered = TRUE, registered_user_id = %s 
            WHERE roster_id = %s
        """
        Database.execute_query(sql, (user_id, roster_id), commit=True)
