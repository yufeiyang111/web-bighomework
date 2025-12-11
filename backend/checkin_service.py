# -*- coding: utf-8 -*-
"""签到服务"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import Database
from config import Config
from pymysql.cursors import DictCursor
import uuid
import hashlib
import json
import numpy as np
from datetime import datetime, timedelta

checkin_bp = Blueprint('checkin', __name__)

def get_db_connection():
    return Database.get_connection()

def get_cursor(conn):
    return conn.cursor(DictCursor)

def get_current_user_id():
    return int(get_jwt_identity())

def generate_checkin_code():
    """生成唯一签到码"""
    return hashlib.md5(f"{uuid.uuid4()}{datetime.now().timestamp()}".encode()).hexdigest()[:8].upper()


@checkin_bp.route('/create', methods=['POST'])
@jwt_required()
def create_checkin():
    """创建签到"""
    user_id = get_current_user_id()
    data = request.json
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        # 验证是否是老师
        cursor.execute("""
            SELECT r.role_name FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id = %s
        """, (user_id,))
        user = cursor.fetchone()
        if not user or user['role_name'] not in ('teacher', 'admin'):
            return jsonify({'success': False, 'message': '只有老师可以发布签到'}), 403
        
        group_id = data.get('group_id')
        title = data.get('title', '课堂签到')
        checkin_type = data.get('type', 'qrcode')
        duration = data.get('duration', 5)
        description = data.get('description', '')
        gesture_number = data.get('gesture_number')  # 手势签到的数字
        location_lat = data.get('location_lat')  # 位置签到的纬度
        location_lng = data.get('location_lng')  # 位置签到的经度
        location_range = data.get('location_range', 50)  # 允许范围（米）
        
        # 手势签到必须指定数字
        if checkin_type == 'gesture':
            if not gesture_number or gesture_number not in [1, 2, 3, 4, 5]:
                return jsonify({'success': False, 'message': '手势签到必须指定1-5的数字'}), 400
        
        # 位置签到必须指定位置
        if checkin_type == 'location':
            if location_lat is None or location_lng is None:
                return jsonify({'success': False, 'message': '位置签到必须指定签到位置'}), 400
        
        # 生成签到码
        checkin_code = generate_checkin_code()
        
        # 计算结束时间
        end_time = datetime.now() + timedelta(minutes=duration)
        
        # 创建签到记录
        cursor.execute("""
            INSERT INTO checkins (group_id, creator_id, title, type, checkin_code, 
                                  duration, end_time, description, gesture_number, 
                                  location_lat, location_lng, location_range, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """, (group_id, user_id, title, checkin_type, checkin_code, 
              duration, end_time, description, gesture_number,
              location_lat, location_lng, location_range))
        
        checkin_id = cursor.lastrowid
        
        # 如果关联了群组，发送群消息通知
        if group_id:
            cursor.execute("""
                INSERT INTO group_messages (group_id, sender_id, message_type, content, reference_id, reference_type)
                VALUES (%s, %s, 'checkin', %s, %s, 'checkin')
            """, (group_id, user_id, f'{title}（限时{duration}分钟）', checkin_id))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'checkin_id': checkin_id,
            'checkin_code': checkin_code,
            'end_time': end_time.isoformat(),
            'message': '签到发布成功'
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/<int:checkin_id>', methods=['GET'])
@jwt_required()
def get_checkin_detail(checkin_id):
    """获取签到详情"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT c.*, u.real_name as creator_name, g.name as group_name
            FROM checkins c
            LEFT JOIN users u ON c.creator_id = u.user_id
            LEFT JOIN chat_groups g ON c.group_id = g.id
            WHERE c.id = %s
        """, (checkin_id,))
        checkin = cursor.fetchone()
        
        if not checkin:
            return jsonify({'success': False, 'message': '签到不存在'}), 404
        
        # 检查签到状态
        if checkin['end_time'] and datetime.now() > checkin['end_time']:
            checkin['status'] = 'ended'
        
        return jsonify({'success': True, 'checkin': checkin})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/<int:checkin_id>/qrcode', methods=['GET'])
@jwt_required()
def get_checkin_qrcode(checkin_id):
    """获取签到二维码数据"""
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT id, checkin_code, title, end_time, status
            FROM checkins WHERE id = %s
        """, (checkin_id,))
        checkin = cursor.fetchone()
        
        if not checkin:
            return jsonify({'success': False, 'message': '签到不存在'}), 404
        
        # 二维码内容：网站签到页面URL（带签到码参数）
        # 优先使用请求来源，否则使用配置的前端URL
        base_url = request.headers.get('Origin') or Config.FRONTEND_URL
        qr_data = f"{base_url}/checkin/scan?code={checkin['checkin_code']}"
        
        return jsonify({
            'success': True,
            'qr_data': qr_data,
            'checkin_code': checkin['checkin_code'],
            'title': checkin['title'],
            'end_time': checkin['end_time'].isoformat() if checkin['end_time'] else None
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/do', methods=['POST'])
@jwt_required()
def do_checkin():
    """学生签到"""
    user_id = get_current_user_id()
    data = request.json
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        checkin_id = data.get('checkin_id')
        checkin_code = data.get('checkin_code', '').upper().strip()
        
        # 如果只有签到码，通过签到码查找签到
        if checkin_code and not checkin_id:
            cursor.execute("""
                SELECT * FROM checkins WHERE checkin_code = %s AND status = 'active'
            """, (checkin_code,))
            checkin = cursor.fetchone()
            if checkin:
                checkin_id = checkin['id']
        else:
            # 获取签到信息
            cursor.execute("""
                SELECT * FROM checkins WHERE id = %s
            """, (checkin_id,))
            checkin = cursor.fetchone()
        
        if not checkin:
            return jsonify({'success': False, 'message': '签到不存在'}), 404
        
        # 验证签到码
        if checkin['type'] == 'qrcode' and checkin['checkin_code'] != checkin_code:
            return jsonify({'success': False, 'message': '签到码错误'}), 400
        
        # 检查是否已过期
        if checkin['end_time'] and datetime.now() > checkin['end_time']:
            return jsonify({'success': False, 'message': '签到已结束'}), 400
        
        # 检查是否已签到
        cursor.execute("""
            SELECT id FROM checkin_records WHERE checkin_id = %s AND user_id = %s
        """, (checkin_id, user_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '您已签到过了'}), 400
        
        # 获取用户信息
        cursor.execute("SELECT real_name FROM users WHERE user_id = %s", (user_id,))
        user = cursor.fetchone()
        
        # 判断是否迟到（超过一半时间）
        status = 'checked'
        if checkin['end_time'] and checkin['created_at']:
            total_seconds = (checkin['end_time'] - checkin['created_at']).total_seconds()
            elapsed_seconds = (datetime.now() - checkin['created_at']).total_seconds()
            if elapsed_seconds > total_seconds * 0.5:
                status = 'late'
        
        # 记录签到
        cursor.execute("""
            INSERT INTO checkin_records (checkin_id, user_id, status, checkin_time)
            VALUES (%s, %s, %s, NOW())
        """, (checkin_id, user_id, status))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'status': status,
            'message': '签到成功' if status == 'checked' else '签到成功（迟到）'
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/<int:checkin_id>/records', methods=['GET'])
@jwt_required()
def get_checkin_records(checkin_id):
    """获取签到记录（已签到/未签到）"""
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        # 获取签到信息
        cursor.execute("""
            SELECT c.*, g.id as group_id FROM checkins c
            LEFT JOIN chat_groups g ON c.group_id = g.id
            WHERE c.id = %s
        """, (checkin_id,))
        checkin = cursor.fetchone()
        
        if not checkin:
            return jsonify({'success': False, 'message': '签到不存在'}), 404
        
        # 获取已签到的人
        cursor.execute("""
            SELECT cr.*, u.real_name, u.photo_url, cr.face_image_url, cr.face_similarity
            FROM checkin_records cr
            JOIN users u ON cr.user_id = u.user_id
            WHERE cr.checkin_id = %s
            ORDER BY cr.checkin_time
        """, (checkin_id,))
        checked_list = cursor.fetchall()
        checked_user_ids = [r['user_id'] for r in checked_list]
        
        # 获取群成员（未签到的）
        unchecked_list = []
        if checkin['group_id']:
            cursor.execute("""
                SELECT gm.user_id, u.real_name, u.photo_url
                FROM group_members gm
                JOIN users u ON gm.user_id = u.user_id
                WHERE gm.group_id = %s AND gm.role = 'member'
            """, (checkin['group_id'],))
            all_members = cursor.fetchall()
            unchecked_list = [m for m in all_members if m['user_id'] not in checked_user_ids]
        
        return jsonify({
            'success': True,
            'checked': checked_list,
            'unchecked': unchecked_list,
            'checked_count': len(checked_list),
            'unchecked_count': len(unchecked_list),
            'total': len(checked_list) + len(unchecked_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/active', methods=['GET'])
@jwt_required()
def get_active_checkins():
    """获取当前用户可参与的进行中签到"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        # 获取用户所在群组的进行中签到
        cursor.execute("""
            SELECT c.*, g.name as group_name, u.real_name as creator_name,
                   (SELECT COUNT(*) FROM checkin_records WHERE checkin_id = c.id) as checked_count
            FROM checkins c
            JOIN chat_groups g ON c.group_id = g.id
            JOIN group_members gm ON g.id = gm.group_id AND gm.user_id = %s
            LEFT JOIN users u ON c.creator_id = u.user_id
            WHERE c.status = 'active' AND c.end_time > NOW()
            ORDER BY c.created_at DESC
        """, (user_id,))
        checkins = cursor.fetchall()
        
        # 检查用户是否已签到
        for c in checkins:
            cursor.execute("""
                SELECT status FROM checkin_records 
                WHERE checkin_id = %s AND user_id = %s
            """, (c['id'], user_id))
            record = cursor.fetchone()
            c['my_status'] = record['status'] if record else None
        
        return jsonify({'success': True, 'checkins': checkins})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/my-created', methods=['GET'])
@jwt_required()
def get_my_created_checkins():
    """获取我创建的签到"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT c.*, g.name as group_name,
                   (SELECT COUNT(*) FROM checkin_records WHERE checkin_id = c.id) as checked_count,
                   (SELECT COUNT(*) FROM group_members WHERE group_id = c.group_id AND role = 'member') as total_count
            FROM checkins c
            LEFT JOIN chat_groups g ON c.group_id = g.id
            WHERE c.creator_id = %s
            ORDER BY c.created_at DESC
            LIMIT 50
        """, (user_id,))
        checkins = cursor.fetchall()
        
        # 更新过期签到状态
        for c in checkins:
            if c['end_time'] and datetime.now() > c['end_time'] and c['status'] == 'active':
                c['status'] = 'ended'
        
        return jsonify({'success': True, 'checkins': checkins})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/history', methods=['GET'])
@jwt_required()
def get_my_checkin_history():
    """获取我的签到历史"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("""
            SELECT cr.*, c.title, c.type, g.name as group_name, cr.face_image_url, cr.face_similarity
            FROM checkin_records cr
            JOIN checkins c ON cr.checkin_id = c.id
            LEFT JOIN chat_groups g ON c.group_id = g.id
            WHERE cr.user_id = %s
            ORDER BY cr.checkin_time DESC
            LIMIT 50
        """, (user_id,))
        records = cursor.fetchall()
        
        return jsonify({'success': True, 'records': records})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/<int:checkin_id>/end', methods=['POST'])
@jwt_required()
def end_checkin(checkin_id):
    """结束签到"""
    user_id = get_current_user_id()
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        cursor.execute("SELECT creator_id FROM checkins WHERE id = %s", (checkin_id,))
        checkin = cursor.fetchone()
        
        if not checkin:
            return jsonify({'success': False, 'message': '签到不存在'}), 404
        
        if checkin['creator_id'] != user_id:
            return jsonify({'success': False, 'message': '只有创建者可以结束签到'}), 403
        
        cursor.execute("""
            UPDATE checkins SET status = 'ended', end_time = NOW() WHERE id = %s
        """, (checkin_id,))
        
        conn.commit()
        return jsonify({'success': True, 'message': '签到已结束'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/face', methods=['POST'])
@jwt_required()
def face_checkin():
    """人脸签到"""
    user_id = get_current_user_id()
    data = request.json
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        checkin_id = data.get('checkin_id')
        face_image = data.get('face_image')  # base64 图片
        liveness_data = data.get('liveness_data', {})
        
        if not checkin_id or not face_image:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        # 获取签到信息
        cursor.execute("""
            SELECT * FROM checkins WHERE id = %s
        """, (checkin_id,))
        checkin = cursor.fetchone()
        
        if not checkin:
            return jsonify({'success': False, 'message': '签到不存在'}), 404
        
        # 检查签到类型
        if checkin['type'] != 'face':
            return jsonify({'success': False, 'message': '该签到不支持人脸签到'}), 400
        
        # 检查是否已过期
        if checkin['end_time'] and datetime.now() > checkin['end_time']:
            return jsonify({'success': False, 'message': '签到已结束'}), 400
        
        # 检查是否已签到
        cursor.execute("""
            SELECT id FROM checkin_records WHERE checkin_id = %s AND user_id = %s
        """, (checkin_id, user_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '您已签到过了'}), 400
        
        # 导入人脸服务
        from face_service import FaceService
        
        # 获取用户已注册的人脸信息
        cursor.execute("""
            SELECT face_embedding FROM user_faces WHERE user_id = %s
        """, (user_id,))
        user_face = cursor.fetchone()
        
        if not user_face:
            return jsonify({'success': False, 'message': '您尚未录入人脸信息，请先在个人中心录入人脸'}), 400
        
        # 验证活体检测
        if not liveness_data.get('blink_detected'):
            return jsonify({'success': False, 'message': '活体检测失败：未检测到眨眼动作'}), 400
        
        if not liveness_data.get('head_turn_detected'):
            return jsonify({'success': False, 'message': '活体检测失败：未检测到转头动作'}), 400
        
        # 提取上传图片的人脸特征
        result = FaceService.extract_embedding_from_base64(face_image)
        if not result['success']:
            return jsonify({'success': False, 'message': result.get('message', '人脸识别失败')}), 400
        
        verify_embedding = np.array(result['embedding'])
        stored_embedding = np.array(json.loads(user_face['face_embedding']))
        
        # 计算相似度
        distance = FaceService.cosine_distance(verify_embedding, stored_embedding)
        similarity = (1 - distance) * 100
        
        # 验证是否匹配（阈值 0.32）
        if distance >= FaceService.THRESHOLD:
            return jsonify({
                'success': False, 
                'message': f'人脸验证失败，相似度不足（{similarity:.1f}%）',
                'similarity': round(similarity, 2)
            }), 400
        
        # 判断是否迟到
        status = 'checked'
        if checkin['end_time'] and checkin['created_at']:
            total_seconds = (checkin['end_time'] - checkin['created_at']).total_seconds()
            elapsed_seconds = (datetime.now() - checkin['created_at']).total_seconds()
            if elapsed_seconds > total_seconds * 0.5:
                status = 'late'
        
        # 保存人脸截图
        import os
        import base64
        face_image_url = None
        try:
            # 创建目录（使用绝对路径）
            import pathlib
            base_dir = pathlib.Path(__file__).parent.absolute()
            upload_dir = base_dir / 'uploads' / 'checkin_faces'
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            print(f'[人脸签到] 保存目录: {upload_dir}')
            
            # 解码并保存图片
            if ',' in face_image:
                face_image_data = face_image.split(',')[1]
            else:
                face_image_data = face_image
            
            img_data = base64.b64decode(face_image_data)
            filename = f"checkin_{checkin_id}_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            filepath = upload_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(img_data)
            
            face_image_url = f'/uploads/checkin_faces/{filename}'
            print(f'[人脸签到] 截图保存成功: {filepath}')
        except Exception as img_err:
            print(f'[人脸签到] 保存人脸截图失败: {img_err}')
            import traceback
            traceback.print_exc()
        
        # 记录签到（包含人脸截图和相似度）
        cursor.execute("""
            INSERT INTO checkin_records (checkin_id, user_id, status, checkin_time, face_image_url, face_similarity)
            VALUES (%s, %s, %s, NOW(), %s, %s)
        """, (checkin_id, user_id, status, face_image_url, round(similarity, 2)))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'status': status,
            'similarity': round(similarity, 2),
            'face_image_url': face_image_url,
            'message': f'人脸签到成功（相似度: {similarity:.1f}%）' if status == 'checked' else f'人脸签到成功（迟到，相似度: {similarity:.1f}%）'
        })
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/gesture', methods=['POST'])
@jwt_required()
def gesture_checkin():
    """手势签到（人脸+手势验证）"""
    user_id = get_current_user_id()
    data = request.json
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        checkin_id = data.get('checkin_id')
        face_image = data.get('face_image')  # base64 图片
        detected_gesture = data.get('detected_gesture')  # 检测到的手势数字
        liveness_data = data.get('liveness_data', {})
        
        if not checkin_id or not face_image:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        if detected_gesture is None:
            return jsonify({'success': False, 'message': '未检测到手势'}), 400
        
        # 获取签到信息
        cursor.execute("""
            SELECT * FROM checkins WHERE id = %s
        """, (checkin_id,))
        checkin = cursor.fetchone()
        
        if not checkin:
            return jsonify({'success': False, 'message': '签到不存在'}), 404
        
        # 检查签到类型
        if checkin['type'] != 'gesture':
            return jsonify({'success': False, 'message': '该签到不支持手势签到'}), 400
        
        # 检查是否已过期
        if checkin['end_time'] and datetime.now() > checkin['end_time']:
            return jsonify({'success': False, 'message': '签到已结束'}), 400
        
        # 检查是否已签到
        cursor.execute("""
            SELECT id FROM checkin_records WHERE checkin_id = %s AND user_id = %s
        """, (checkin_id, user_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '您已签到过了'}), 400
        
        # 验证手势数字
        required_gesture = checkin.get('gesture_number')
        if required_gesture and int(detected_gesture) != int(required_gesture):
            return jsonify({
                'success': False, 
                'message': f'手势错误，请比出数字 {required_gesture}'
            }), 400
        
        # 导入人脸服务
        from face_service import FaceService
        
        # 获取用户已注册的人脸信息
        cursor.execute("""
            SELECT face_embedding FROM user_faces WHERE user_id = %s
        """, (user_id,))
        user_face = cursor.fetchone()
        
        if not user_face:
            return jsonify({'success': False, 'message': '您尚未录入人脸信息，请先在个人中心录入人脸'}), 400
        
        # 提取上传图片的人脸特征
        result = FaceService.extract_embedding_from_base64(face_image)
        if not result['success']:
            return jsonify({'success': False, 'message': result.get('message', '人脸识别失败')}), 400
        
        verify_embedding = np.array(result['embedding'])
        stored_embedding = np.array(json.loads(user_face['face_embedding']))
        
        # 计算相似度
        distance = FaceService.cosine_distance(verify_embedding, stored_embedding)
        similarity = (1 - distance) * 100
        
        # 验证是否匹配（阈值 0.32）
        if distance >= FaceService.THRESHOLD:
            return jsonify({
                'success': False, 
                'message': f'人脸验证失败，相似度不足（{similarity:.1f}%）',
                'similarity': round(similarity, 2)
            }), 400
        
        # 判断是否迟到
        status = 'checked'
        if checkin['end_time'] and checkin['created_at']:
            total_seconds = (checkin['end_time'] - checkin['created_at']).total_seconds()
            elapsed_seconds = (datetime.now() - checkin['created_at']).total_seconds()
            if elapsed_seconds > total_seconds * 0.5:
                status = 'late'
        
        # 保存人脸截图
        import os
        import base64
        face_image_url = None
        try:
            import pathlib
            base_dir = pathlib.Path(__file__).parent.absolute()
            upload_dir = base_dir / 'uploads' / 'checkin_faces'
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            if ',' in face_image:
                face_image_data = face_image.split(',')[1]
            else:
                face_image_data = face_image
            
            img_data = base64.b64decode(face_image_data)
            filename = f"gesture_{checkin_id}_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            filepath = upload_dir / filename
            
            with open(filepath, 'wb') as f:
                f.write(img_data)
            
            face_image_url = f'/uploads/checkin_faces/{filename}'
        except Exception as img_err:
            print(f'[手势签到] 保存截图失败: {img_err}')
        
        # 记录签到
        cursor.execute("""
            INSERT INTO checkin_records (checkin_id, user_id, status, checkin_time, face_image_url, face_similarity)
            VALUES (%s, %s, %s, NOW(), %s, %s)
        """, (checkin_id, user_id, status, face_image_url, round(similarity, 2)))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'status': status,
            'similarity': round(similarity, 2),
            'detected_gesture': detected_gesture,
            'face_image_url': face_image_url,
            'message': f'手势签到成功（手势: {detected_gesture}，相似度: {similarity:.1f}%）'
        })
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/location', methods=['POST'])
@jwt_required()
def location_checkin():
    """位置签到"""
    user_id = get_current_user_id()
    data = request.json
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        checkin_id = data.get('checkin_id')
        user_lat = data.get('latitude')
        user_lng = data.get('longitude')
        
        if not checkin_id or user_lat is None or user_lng is None:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        # 获取签到信息
        cursor.execute("""
            SELECT * FROM checkins WHERE id = %s
        """, (checkin_id,))
        checkin = cursor.fetchone()
        
        if not checkin:
            return jsonify({'success': False, 'message': '签到不存在'}), 404
        
        # 检查签到类型
        if checkin['type'] != 'location':
            return jsonify({'success': False, 'message': '该签到不支持位置签到'}), 400
        
        # 检查是否已过期
        if checkin['end_time'] and datetime.now() > checkin['end_time']:
            return jsonify({'success': False, 'message': '签到已结束'}), 400
        
        # 检查是否已签到
        cursor.execute("""
            SELECT id FROM checkin_records WHERE checkin_id = %s AND user_id = %s
        """, (checkin_id, user_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': '您已签到过了'}), 400
        
        # 计算距离
        target_lat = float(checkin['location_lat']) if checkin['location_lat'] else None
        target_lng = float(checkin['location_lng']) if checkin['location_lng'] else None
        
        if target_lat is None or target_lng is None:
            return jsonify({'success': False, 'message': '签到位置未设置'}), 400
        
        # 使用 Haversine 公式计算距离
        import math
        R = 6371000  # 地球半径（米）
        
        lat1, lat2 = math.radians(float(user_lat)), math.radians(target_lat)
        delta_lat = math.radians(target_lat - float(user_lat))
        delta_lng = math.radians(target_lng - float(user_lng))
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        # 获取允许的范围（默认50米）
        allowed_range = checkin.get('location_range') or 50
        
        if distance > allowed_range:
            return jsonify({
                'success': False,
                'message': f'距离签到点太远（{distance:.0f}米），需在{allowed_range}米范围内',
                'distance': round(distance, 1)
            }), 400
        
        # 判断是否迟到
        status = 'checked'
        if checkin['end_time'] and checkin['created_at']:
            total_seconds = (checkin['end_time'] - checkin['created_at']).total_seconds()
            elapsed_seconds = (datetime.now() - checkin['created_at']).total_seconds()
            if elapsed_seconds > total_seconds * 0.5:
                status = 'late'
        
        # 记录签到
        cursor.execute("""
            INSERT INTO checkin_records (checkin_id, user_id, status, checkin_time, location_lat, location_lng)
            VALUES (%s, %s, %s, NOW(), %s, %s)
        """, (checkin_id, user_id, status, user_lat, user_lng))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'status': status,
            'distance': round(distance, 1),
            'message': f'位置签到成功（距离: {distance:.0f}米）' if status == 'checked' else f'位置签到成功（迟到，距离: {distance:.0f}米）'
        })
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@checkin_bp.route('/smart-checkin', methods=['POST'])
@jwt_required()
def smart_checkin():
    """智能点到 - 通过班级合照识别签到"""
    user_id = get_current_user_id()
    data = request.json
    
    conn = get_db_connection()
    cursor = get_cursor(conn)
    
    try:
        checkin_id = data.get('checkin_id')
        class_photo = data.get('class_photo')  # base64 图片
        
        if not checkin_id or not class_photo:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        # 获取签到信息
        cursor.execute("""
            SELECT c.*, g.id as group_id FROM checkins c
            LEFT JOIN chat_groups g ON c.group_id = g.id
            WHERE c.id = %s
        """, (checkin_id,))
        checkin = cursor.fetchone()
        
        if not checkin:
            return jsonify({'success': False, 'message': '签到不存在'}), 404
        
        # 验证是否是创建者
        if checkin['creator_id'] != user_id:
            return jsonify({'success': False, 'message': '只有创建者可以使用智能点到'}), 403
        
        # 检查签到类型
        if checkin['type'] != 'photo':
            return jsonify({'success': False, 'message': '该签到不支持智能点到'}), 400
        
        # 导入人脸服务
        from face_service import FaceService
        import base64
        import cv2
        import numpy as np
        
        # 解码图片
        if ',' in class_photo:
            class_photo = class_photo.split(',')[1]
        img_data = base64.b64decode(class_photo)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return jsonify({'success': False, 'message': '图片解码失败'}), 400
        
        # 检测图片中的所有人脸
        detected_faces = FaceService.detect_all_faces(img)
        
        if not detected_faces:
            return jsonify({
                'success': False, 
                'message': '未在照片中检测到人脸',
                'detected_count': 0
            }), 400
        
        print(f'[智能点到] 检测到 {len(detected_faces)} 张人脸')
        
        # 获取群组所有成员的人脸信息
        cursor.execute("""
            SELECT gm.user_id, u.real_name, uf.face_embedding
            FROM group_members gm
            JOIN users u ON gm.user_id = u.user_id
            LEFT JOIN user_faces uf ON gm.user_id = uf.user_id
            WHERE gm.group_id = %s AND gm.role = 'member'
        """, (checkin['group_id'],))
        members = cursor.fetchall()
        
        # 过滤出有人脸信息的成员
        members_with_face = [m for m in members if m['face_embedding']]
        print(f'[智能点到] 群组有 {len(members)} 名成员，其中 {len(members_with_face)} 人有人脸信息')
        
        # 获取已签到的用户
        cursor.execute("""
            SELECT user_id FROM checkin_records WHERE checkin_id = %s
        """, (checkin_id,))
        checked_users = set(r['user_id'] for r in cursor.fetchall())
        
        # 匹配人脸
        matched_users = []
        for face_embedding in detected_faces:
            face_vec = np.array(face_embedding)
            
            best_match = None
            best_distance = float('inf')
            
            for member in members_with_face:
                if member['user_id'] in checked_users:
                    continue  # 已签到的跳过
                
                stored_vec = np.array(json.loads(member['face_embedding']))
                distance = FaceService.cosine_distance(face_vec, stored_vec)
                
                if distance < FaceService.THRESHOLD and distance < best_distance:
                    best_distance = distance
                    best_match = member
            
            if best_match and best_match['user_id'] not in [m['user_id'] for m in matched_users]:
                similarity = (1 - best_distance) * 100
                matched_users.append({
                    'user_id': best_match['user_id'],
                    'real_name': best_match['real_name'],
                    'similarity': round(similarity, 1)
                })
                checked_users.add(best_match['user_id'])
        
        print(f'[智能点到] 匹配到 {len(matched_users)} 名学生')
        
        # 批量签到
        checkin_count = 0
        for user in matched_users:
            try:
                # 判断是否迟到
                status = 'checked'
                if checkin['end_time'] and checkin['created_at']:
                    total_seconds = (checkin['end_time'] - checkin['created_at']).total_seconds()
                    elapsed_seconds = (datetime.now() - checkin['created_at']).total_seconds()
                    if elapsed_seconds > total_seconds * 0.5:
                        status = 'late'
                
                cursor.execute("""
                    INSERT INTO checkin_records (checkin_id, user_id, status, checkin_time, face_similarity)
                    VALUES (%s, %s, %s, NOW(), %s)
                """, (checkin_id, user['user_id'], status, user['similarity']))
                checkin_count += 1
            except Exception as e:
                print(f'[智能点到] 签到失败 user_id={user["user_id"]}: {e}')
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'message': f'智能点到完成，识别到 {len(detected_faces)} 张人脸，成功签到 {checkin_count} 人',
            'detected_count': len(detected_faces),
            'matched_count': len(matched_users),
            'checkin_count': checkin_count,
            'matched_users': matched_users
        })
    except Exception as e:
        conn.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()
