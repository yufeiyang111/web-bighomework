"""
人脸识别服务
使用 DeepFace 进行人脸特征提取和比对
使用 MediaPipe 进行活体检测（眨眼、转头）
"""
import os
import json
import base64
import numpy as np
from PIL import Image
from io import BytesIO
from datetime import datetime
from werkzeug.utils import secure_filename
from database import Database
from config import Config

# 延迟导入
_deepface = None
_mp_face_mesh = None
_mp_drawing = None

def get_deepface():
    """延迟加载 DeepFace"""
    global _deepface
    if _deepface is None:
        from deepface import DeepFace
        _deepface = DeepFace
    return _deepface

def get_mediapipe():
    """延迟加载 MediaPipe"""
    global _mp_face_mesh, _mp_drawing
    if _mp_face_mesh is None:
        import mediapipe as mp
        _mp_face_mesh = mp.solutions.face_mesh
        _mp_drawing = mp.solutions.drawing_utils
    return _mp_face_mesh, _mp_drawing


class LivenessDetector:
    """活体检测器 - 检测眨眼和转头动作"""
    
    # 眼睛关键点索引 (MediaPipe Face Mesh)
    LEFT_EYE = [362, 385, 387, 263, 373, 380]
    RIGHT_EYE = [33, 160, 158, 133, 153, 144]
    
    # 阈值
    EAR_THRESHOLD = 0.21  # 眼睛纵横比阈值，低于此值认为闭眼
    HEAD_TURN_THRESHOLD = 0.15  # 转头阈值
    
    @staticmethod
    def calculate_ear(eye_landmarks):
        """计算眼睛纵横比 (Eye Aspect Ratio)"""
        # 垂直距离
        v1 = np.linalg.norm(np.array(eye_landmarks[1]) - np.array(eye_landmarks[5]))
        v2 = np.linalg.norm(np.array(eye_landmarks[2]) - np.array(eye_landmarks[4]))
        # 水平距离
        h = np.linalg.norm(np.array(eye_landmarks[0]) - np.array(eye_landmarks[3]))
        # EAR
        ear = (v1 + v2) / (2.0 * h) if h > 0 else 0
        return ear
    
    @staticmethod
    def detect_blink(frame_data):
        """检测眨眼动作"""
        try:
            mp_face_mesh, _ = get_mediapipe()
            import cv2
            
            # 解码图片
            if isinstance(frame_data, str):
                # base64 字符串
                img_data = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                frame = frame_data
            
            if frame is None:
                return {'detected': False, 'ear': 0}
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            with mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5
            ) as face_mesh:
                results = face_mesh.process(rgb_frame)
                
                if not results.multi_face_landmarks:
                    return {'detected': False, 'ear': 0, 'message': '未检测到人脸'}
                
                landmarks = results.multi_face_landmarks[0].landmark
                h, w = frame.shape[:2]
                
                # 获取眼睛关键点坐标
                left_eye = [(landmarks[i].x * w, landmarks[i].y * h) for i in LivenessDetector.LEFT_EYE]
                right_eye = [(landmarks[i].x * w, landmarks[i].y * h) for i in LivenessDetector.RIGHT_EYE]
                
                # 计算双眼EAR
                left_ear = LivenessDetector.calculate_ear(left_eye)
                right_ear = LivenessDetector.calculate_ear(right_eye)
                avg_ear = (left_ear + right_ear) / 2
                
                is_blink = avg_ear < LivenessDetector.EAR_THRESHOLD
                
                return {
                    'detected': True,
                    'ear': round(avg_ear, 3),
                    'is_blink': is_blink
                }
        except Exception as e:
            return {'detected': False, 'ear': 0, 'error': str(e)}
    
    @staticmethod
    def detect_head_pose(frame_data):
        """检测头部姿态（左右转头）"""
        try:
            mp_face_mesh, _ = get_mediapipe()
            import cv2
            
            # 解码图片
            if isinstance(frame_data, str):
                img_data = base64.b64decode(frame_data.split(',')[1] if ',' in frame_data else frame_data)
                nparr = np.frombuffer(img_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                frame = frame_data
            
            if frame is None:
                return {'detected': False, 'direction': 'unknown'}
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            with mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=True,
                min_detection_confidence=0.5
            ) as face_mesh:
                results = face_mesh.process(rgb_frame)
                
                if not results.multi_face_landmarks:
                    return {'detected': False, 'direction': 'unknown', 'message': '未检测到人脸'}
                
                landmarks = results.multi_face_landmarks[0].landmark
                
                # 使用鼻尖和脸部两侧点计算头部朝向
                nose_tip = landmarks[1]  # 鼻尖
                left_face = landmarks[234]  # 左脸
                right_face = landmarks[454]  # 右脸
                
                # 计算鼻尖相对于脸部中心的偏移
                face_center_x = (left_face.x + right_face.x) / 2
                nose_offset = nose_tip.x - face_center_x
                
                # 判断方向
                if nose_offset < -LivenessDetector.HEAD_TURN_THRESHOLD:
                    direction = 'left'
                elif nose_offset > LivenessDetector.HEAD_TURN_THRESHOLD:
                    direction = 'right'
                else:
                    direction = 'center'
                
                return {
                    'detected': True,
                    'direction': direction,
                    'offset': round(nose_offset, 3)
                }
        except Exception as e:
            return {'detected': False, 'direction': 'unknown', 'error': str(e)}


class FaceService:
    """人脸识别服务类"""
    
    FACE_FOLDER = 'uploads/faces'
    MODEL_NAME = 'Facenet'  # 使用 Facenet 模型，128维特征向量
    DETECTOR_BACKEND = 'retinaface'  # 使用 RetinaFace 检测器，精度高
    DISTANCE_METRIC = 'cosine'
    THRESHOLD = 0.32  # 更严格的阈值，提高识别精度
    
    @staticmethod
    def init_folders():
        """初始化文件夹"""
        os.makedirs(FaceService.FACE_FOLDER, exist_ok=True)
    
    @staticmethod
    def save_face_image(image_file, user_id):
        """保存人脸图片"""
        FaceService.init_folders()
        filename = secure_filename(f"face_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
        filepath = os.path.join(FaceService.FACE_FOLDER, filename)
        
        # 压缩并保存图片
        img = Image.open(image_file)
        img = img.convert('RGB')
        img.thumbnail((640, 640))
        img.save(filepath, 'JPEG', quality=90)
        
        return filepath
    
    @staticmethod
    def decode_base64_image(base64_str):
        """解码 base64 图片"""
        try:
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            img_data = base64.b64decode(base64_str)
            img = Image.open(BytesIO(img_data))
            return img.convert('RGB')
        except Exception as e:
            return None
    
    @staticmethod
    def extract_face_embedding(image_path):
        """提取人脸特征向量"""
        try:
            DeepFace = get_deepface()
            
            embedding_objs = DeepFace.represent(
                img_path=image_path,
                model_name=FaceService.MODEL_NAME,
                enforce_detection=True,
                detector_backend=FaceService.DETECTOR_BACKEND
            )
            
            if not embedding_objs:
                return {'success': False, 'message': '未检测到人脸'}
            
            embedding = embedding_objs[0]['embedding']
            
            return {
                'success': True,
                'embedding': embedding,
                'face_count': len(embedding_objs)
            }
            
        except Exception as e:
            error_msg = str(e)
            if 'Face could not be detected' in error_msg:
                return {'success': False, 'message': '未检测到人脸，请确保照片清晰且包含正面人脸'}
            return {'success': False, 'message': f'人脸特征提取失败: {error_msg}'}
    
    @staticmethod
    def extract_embedding_from_base64(base64_str):
        """从 base64 图片提取特征"""
        try:
            import cv2
            DeepFace = get_deepface()
            
            # 解码 base64
            if ',' in base64_str:
                base64_str = base64_str.split(',')[1]
            img_data = base64.b64decode(base64_str)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {'success': False, 'message': '图片解码失败'}
            
            # 转换为 RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            embedding_objs = DeepFace.represent(
                img_path=img_rgb,
                model_name=FaceService.MODEL_NAME,
                enforce_detection=True,
                detector_backend=FaceService.DETECTOR_BACKEND
            )
            
            if not embedding_objs:
                return {'success': False, 'message': '未检测到人脸'}
            
            return {
                'success': True,
                'embedding': embedding_objs[0]['embedding']
            }
        except Exception as e:
            error_msg = str(e)
            if 'Face could not be detected' in error_msg:
                return {'success': False, 'message': '未检测到人脸'}
            return {'success': False, 'message': f'特征提取失败: {error_msg}'}
    
    @staticmethod
    def register_face(user_id, image_file):
        """注册用户人脸"""
        try:
            # 保存图片
            image_path = FaceService.save_face_image(image_file, user_id)
            
            # 提取特征
            result = FaceService.extract_face_embedding(image_path)
            
            if not result['success']:
                if os.path.exists(image_path):
                    os.remove(image_path)
                return result
            
            embedding = result['embedding']
            
            # 检查是否已有人脸数据
            check_sql = "SELECT face_id FROM user_faces WHERE user_id = %s"
            existing = Database.execute_query(check_sql, (user_id,), fetch_one=True)
            
            if existing:
                update_sql = """
                    UPDATE user_faces 
                    SET face_image_path = %s, face_embedding = %s, updated_at = NOW()
                    WHERE user_id = %s
                """
                Database.execute_query(update_sql, (image_path, json.dumps(embedding), user_id), commit=True)
            else:
                insert_sql = """
                    INSERT INTO user_faces (user_id, face_image_path, face_embedding)
                    VALUES (%s, %s, %s)
                """
                Database.execute_query(insert_sql, (user_id, image_path, json.dumps(embedding)), commit=True)
            
            return {'success': True, 'message': '人脸信息录入成功'}
            
        except Exception as e:
            return {'success': False, 'message': f'人脸录入失败: {str(e)}'}
    
    @staticmethod
    def verify_face_with_liveness(face_image_base64, liveness_data):
        """
        带活体检测的人脸验证
        
        Args:
            face_image_base64: 人脸图片的 base64 编码
            liveness_data: 活体检测数据 {blink_detected, head_turn_detected}
        """
        try:
            # 验证活体检测是否通过
            if not liveness_data.get('blink_detected'):
                return {'success': False, 'message': '活体检测失败：未检测到眨眼动作'}
            
            if not liveness_data.get('head_turn_detected'):
                return {'success': False, 'message': '活体检测失败：未检测到转头动作'}
            
            # 提取人脸特征
            result = FaceService.extract_embedding_from_base64(face_image_base64)
            
            if not result['success']:
                return result
            
            verify_embedding = np.array(result['embedding'])
            
            # 查询数据库中的人脸数据
            sql = """
                SELECT uf.user_id, uf.face_embedding, u.email, u.real_name, u.system_account, r.role_name
                FROM user_faces uf
                JOIN users u ON uf.user_id = u.user_id
                JOIN roles r ON u.role_id = r.role_id
                WHERE u.is_active = TRUE AND u.is_verified = TRUE
            """
            faces = Database.execute_query(sql, fetch_all=True)
            
            if not faces:
                return {'success': False, 'message': '未找到已注册的人脸信息'}
            
            # 比对人脸
            best_match = None
            best_distance = float('inf')
            
            for face in faces:
                stored_embedding = np.array(json.loads(face['face_embedding']))
                distance = FaceService.cosine_distance(verify_embedding, stored_embedding)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = face
            
            # 判断是否匹配
            if best_distance < FaceService.THRESHOLD:
                similarity = (1 - best_distance) * 100
                return {
                    'success': True,
                    'matched': True,
                    'user_id': best_match['user_id'],
                    'email': best_match['email'],
                    'real_name': best_match['real_name'],
                    'system_account': best_match['system_account'],
                    'role_name': best_match['role_name'],
                    'similarity': round(similarity, 2),
                    'message': '人脸验证成功'
                }
            else:
                return {
                    'success': True,
                    'matched': False,
                    'message': '人脸验证失败，未找到匹配的用户'
                }
                
        except Exception as e:
            return {'success': False, 'message': f'人脸验证失败: {str(e)}'}
    
    @staticmethod
    def verify_face(image_file, user_id=None):
        """验证人脸（兼容旧接口）"""
        try:
            FaceService.init_folders()
            temp_filename = f"temp_verify_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.jpg"
            temp_path = os.path.join(FaceService.FACE_FOLDER, temp_filename)
            
            img = Image.open(image_file)
            img = img.convert('RGB')
            img.thumbnail((640, 640))
            img.save(temp_path, 'JPEG', quality=90)
            
            result = FaceService.extract_face_embedding(temp_path)
            
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            if not result['success']:
                return result
            
            verify_embedding = np.array(result['embedding'])
            
            if user_id:
                sql = """
                    SELECT uf.user_id, uf.face_embedding, u.email, u.real_name, u.system_account, r.role_name
                    FROM user_faces uf
                    JOIN users u ON uf.user_id = u.user_id
                    JOIN roles r ON u.role_id = r.role_id
                    WHERE uf.user_id = %s AND u.is_active = TRUE
                """
                faces = Database.execute_query(sql, (user_id,), fetch_all=True)
            else:
                sql = """
                    SELECT uf.user_id, uf.face_embedding, u.email, u.real_name, u.system_account, r.role_name
                    FROM user_faces uf
                    JOIN users u ON uf.user_id = u.user_id
                    JOIN roles r ON u.role_id = r.role_id
                    WHERE u.is_active = TRUE AND u.is_verified = TRUE
                """
                faces = Database.execute_query(sql, fetch_all=True)
            
            if not faces:
                return {'success': False, 'message': '未找到已注册的人脸信息'}
            
            best_match = None
            best_distance = float('inf')
            
            for face in faces:
                stored_embedding = np.array(json.loads(face['face_embedding']))
                distance = FaceService.cosine_distance(verify_embedding, stored_embedding)
                
                if distance < best_distance:
                    best_distance = distance
                    best_match = face
            
            if best_distance < FaceService.THRESHOLD:
                similarity = (1 - best_distance) * 100
                return {
                    'success': True,
                    'matched': True,
                    'user_id': best_match['user_id'],
                    'email': best_match['email'],
                    'real_name': best_match['real_name'],
                    'system_account': best_match['system_account'],
                    'role_name': best_match['role_name'],
                    'similarity': round(similarity, 2),
                    'message': '人脸验证成功'
                }
            else:
                return {
                    'success': True,
                    'matched': False,
                    'message': '人脸验证失败，未找到匹配的用户'
                }
                
        except Exception as e:
            return {'success': False, 'message': f'人脸验证失败: {str(e)}'}
    
    @staticmethod
    def cosine_distance(embedding1, embedding2):
        """计算余弦距离"""
        dot_product = np.dot(embedding1, embedding2)
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)
        similarity = dot_product / (norm1 * norm2)
        return 1 - similarity
    
    @staticmethod
    def detect_all_faces(img):
        """检测图片中的所有人脸并提取特征向量
        
        Args:
            img: OpenCV 格式的图片 (numpy array, BGR)
        
        Returns:
            list: 所有检测到的人脸特征向量列表
        """
        try:
            DeepFace = get_deepface()
            import cv2
            
            # 转换为 RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # 保存临时文件（DeepFace 需要文件路径）
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                tmp_path = tmp.name
                cv2.imwrite(tmp_path, img)
            
            try:
                # 提取所有人脸的特征
                embedding_objs = DeepFace.represent(
                    img_path=tmp_path,
                    model_name=FaceService.MODEL_NAME,
                    enforce_detection=False,  # 不强制检测，允许检测多张脸
                    detector_backend=FaceService.DETECTOR_BACKEND
                )
                
                embeddings = [obj['embedding'] for obj in embedding_objs if obj.get('embedding')]
                print(f'[detect_all_faces] 检测到 {len(embeddings)} 张人脸')
                return embeddings
            finally:
                # 删除临时文件
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                    
        except Exception as e:
            print(f'[detect_all_faces] 检测失败: {e}')
            import traceback
            traceback.print_exc()
            return []
    
    @staticmethod
    def has_face_registered(user_id):
        """检查用户是否已注册人脸"""
        sql = "SELECT face_id FROM user_faces WHERE user_id = %s"
        result = Database.execute_query(sql, (user_id,), fetch_one=True)
        return result is not None
    
    @staticmethod
    def delete_face(user_id):
        """删除用户人脸信息"""
        try:
            sql = "SELECT face_image_path FROM user_faces WHERE user_id = %s"
            result = Database.execute_query(sql, (user_id,), fetch_one=True)
            
            if result and result['face_image_path']:
                if os.path.exists(result['face_image_path']):
                    os.remove(result['face_image_path'])
            
            delete_sql = "DELETE FROM user_faces WHERE user_id = %s"
            Database.execute_query(delete_sql, (user_id,), commit=True)
            
            return {'success': True, 'message': '人脸信息已删除'}
        except Exception as e:
            return {'success': False, 'message': f'删除失败: {str(e)}'}
