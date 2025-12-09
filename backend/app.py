# Gevent monkey patching - 必须在所有其他导入之前
from gevent import monkey
monkey.patch_all()

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from config import Config
from database import Database
from user_service import UserService
from email_service import EmailService
from chatbot_service import ChatbotService
from student_roster_service import StudentRosterService
from face_service import FaceService
from message_service import MessageService
from websocket_server import socketio, init_socketio

app = Flask(__name__)

# 配置Flask
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = Config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=Config.JWT_ACCESS_TOKEN_EXPIRES)

# 设置JWT token位置 - 从 header 中读取
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# 初始化CORS
CORS(app, resources={r"/*": {"origins": "*"}})

# 初始化JWT
jwt = JWTManager(app)

# JWT错误处理 - 将422错误改为401
@jwt.invalid_token_loader
def invalid_token_callback(error_string):
    print(f"Token无效: {error_string}")
    return jsonify({
        'success': False,
        'message': 'Token无效，请重新登录'
    }), 401

@jwt.unauthorized_loader
def unauthorized_callback(error_string):
    return jsonify({
        'success': False,
        'message': '缺少Token，请先登录'
    }), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'success': False,
        'message': 'Token已过期，请重新登录'
    }), 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'success': False,
        'message': 'Token已失效，请重新登录'
    }), 401

# Token黑名单检查
@jwt.token_in_blocklist_loader
def check_if_token_in_blocklist(jwt_header, jwt_payload):
    """检查token是否在黑名单中"""
    jti = jwt_payload['jti']
    query = "SELECT token_id FROM token_blacklist WHERE token = %s"
    result = Database.execute_query(query, (jti,), fetch_one=True)
    return result is not None

# ==================== 认证相关路由 ====================

@app.route('/api/auth/send-code', methods=['POST'])
def send_verification_code():
    """发送邮箱验证码"""
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'success': False, 'message': '邮箱不能为空'}), 400
        
        # 检查冷却时间
        can_send, remaining = EmailService.check_cooldown(email)
        if not can_send:
            return jsonify({
                'success': False,
                'message': f'请等待{remaining}秒后再试'
            }), 429
        
        # 生成并发送验证码
        code = EmailService.generate_verification_code()
        
        # 保存到数据库
        if not EmailService.save_verification_code(email, code):
            return jsonify({'success': False, 'message': '保存验证码失败'}), 500
        
        # 发送邮件
        if EmailService.send_verification_email(email, code):
            return jsonify({
                'success': True,
                'message': '验证码已发送，请查收邮件'
            })
        else:
            return jsonify({
                'success': False,
                'message': '发送验证码失败，请检查邮箱配置'
            }), 500
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        print("\n" + "="*80)
        print("[注册] 开始处理注册请求")
        print(f"[注册] 表单数据: {dict(request.form)}")
        print(f"[注册] 文件列表: {list(request.files.keys())}")
        
        # 获取表单数据
        email = request.form.get('email')
        password = request.form.get('password')
        role_name = request.form.get('role', 'student')  # 默认学生
        verification_code = request.form.get('verificationCode')
        real_name = request.form.get('realName')
        student_number = request.form.get('studentNumber')
        roster_id = request.form.get('rosterId')  # 学生花名册ID
        
        print(f"[注册] email: {email}")
        print(f"[注册] role: {role_name}")
        print(f"[注册] realName: {real_name}")
        print(f"[注册] studentNumber: {student_number}")
        print(f"[注册] rosterId: {roster_id}")
        
        # 验证必填字段
        if not all([email, password, verification_code]):
            print("[注册] 失败: 必填字段为空")
            print("="*80 + "\n")
            return jsonify({'success': False, 'message': '请填写所有必填字段'}), 400
        
        # 学生必须提供roster_id（人脸验证后获得）
        if role_name == 'student' and not roster_id:
            print(f"[注册] 失败: 学生未提供 rosterId")
            print(f"[注册] role_name: '{role_name}', roster_id: '{roster_id}'")
            print("="*80 + "\n")
            return jsonify({'success': False, 'message': '学生必须先完成人脸验证'}), 400
        
        # 验证邮箱验证码
        if not EmailService.verify_code(email, verification_code):
            print("[注册] 失败: 验证码错误")
            print("="*80 + "\n")
            return jsonify({'success': False, 'message': '验证码错误或已过期'}), 400
        
        # 处理照片上传
        photo_file = request.files.get('photo')
        print(f"[注册] 照片文件: {photo_file.filename if photo_file else 'None'}")
        
        # 创建用户
        print(f"[注册] 调用 UserService.create_user...")
        result = UserService.create_user(
            email=email,
            password=password,
            role_name=role_name,
            real_name=real_name,
            student_number=student_number,
            photo_file=photo_file,
            roster_id=roster_id  # 传递roster_id
        )
        
        print(f"[注册] UserService.create_user 结果: {result}")
        
        if result['success']:
            # 自动验证邮箱
            UserService.verify_email(email)
            print(f"[注册] 成功!")
            print("="*80 + "\n")
            return jsonify(result), 201
        else:
            print(f"[注册] 失败: {result.get('message')}")
            print("="*80 + "\n")
            return jsonify(result), 400
    
    except Exception as e:
        print(f"[注册] 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*80 + "\n")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not all([email, password]):
            return jsonify({'success': False, 'message': '请填写邮箱和密码'}), 400
        
        # 认证用户
        result = UserService.authenticate(email, password)
        
        if not result['success']:
            return jsonify(result), 401
        
        user = result['user']
        
        # 获取用户权限
        permissions = UserService.get_user_permissions(user['user_id'])
        
        # 创建JWT token
        additional_claims = {
            'role': user['role_name'],
            'permissions': permissions
        }
        access_token = create_access_token(
            identity=str(user['user_id']),  # 转换为字符串
            additional_claims=additional_claims
        )
        
        # 返回用户信息和token
        return jsonify({
            'success': True,
            'message': '登录成功',
            'token': access_token,
            'userInfo': {
                'userId': user['user_id'],
                'systemAccount': user['system_account'],
                'email': user['email'],
                'realName': user['real_name'],
                'role': user['role_name'],
                'permissions': permissions,
                'photoUrl': user['photo_url'],
                'isApproved': user['is_approved']
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    try:
        jti = get_jwt()['jti']
        
        # 将token加入黑名单
        query = "INSERT INTO token_blacklist (token) VALUES (%s)"
        Database.execute_query(query, (jti,), commit=True)
        
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/verify-token', methods=['GET'])
@jwt_required()
def verify_token():
    """验证Token"""
    try:
        user_id = int(get_jwt_identity())  # 转换回整数
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        permissions = UserService.get_user_permissions(user_id)
        
        return jsonify({
            'success': True,
            'userInfo': {
                'userId': user['user_id'],
                'systemAccount': user['system_account'],
                'email': user['email'],
                'realName': user['real_name'],
                'role': user['role_name'],
                'permissions': permissions,
                'photoUrl': user['photo_url'],
                'isApproved': user['is_approved']
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 用户管理路由 ====================

@app.route('/api/users/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户信息"""
    try:
        user_id = int(get_jwt_identity())  # 转换回整数
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        return jsonify({
            'success': True,
            'user': user
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/search', methods=['GET'])
@jwt_required()
def search_user():
    """通过系统账号查找用户"""
    try:
        system_account = request.args.get('account')
        
        if not system_account:
            return jsonify({'success': False, 'message': '请提供系统账号'}), 400
        
        user = UserService.get_user_by_system_account(system_account)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        return jsonify({
            'success': True,
            'user': user
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/users/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """修改密码"""
    try:
        user_id = int(get_jwt_identity())  # 转换回整数
        data = request.get_json()
        
        old_password = data.get('oldPassword')
        new_password = data.get('newPassword')
        
        if not all([old_password, new_password]):
            return jsonify({'success': False, 'message': '请填写所有字段'}), 400
        
        # 验证旧密码
        user = UserService.get_user_by_id(user_id)
        from werkzeug.security import check_password_hash
        
        query = "SELECT password_hash FROM users WHERE user_id = %s"
        result = Database.execute_query(query, (user_id,), fetch_one=True)
        
        if not check_password_hash(result['password_hash'], old_password):
            return jsonify({'success': False, 'message': '原密码错误'}), 400
        
        # 更新密码
        UserService.update_password(user_id, new_password)
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 管理员路由 ====================

@app.route('/api/admin/pending-teachers', methods=['GET'])
@jwt_required()
def get_pending_teachers():
    """获取待审核教师列表（管理员）"""
    try:
        # 验证是否为管理员
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        teachers = UserService.get_pending_teachers()
        
        return jsonify({
            'success': True,
            'teachers': teachers
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/approve-teacher', methods=['POST'])
@jwt_required()
def approve_teacher():
    """审核教师（管理员）"""
    try:
        # 验证是否为管理员
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        admin_id = int(get_jwt_identity())  # 转换回整数
        data = request.get_json()
        
        approval_id = data.get('approvalId')
        approved = data.get('approved')
        note = data.get('note')
        
        if approval_id is None or approved is None:
            return jsonify({'success': False, 'message': '参数不完整'}), 400
        
        result = UserService.approve_teacher(approval_id, admin_id, approved, note)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 健康检查 ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

# 错误处理
@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'message': '接口不存在'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'success': False, 'message': '服务器内部错误'}), 500

# ==================== AI聊天机器人路由 ====================

@app.route('/api/chatbot/sessions', methods=['GET'])
@jwt_required()
def get_chat_sessions():
    """获取用户的聊天会话列表"""
    try:
        user_id = int(get_jwt_identity())
        sessions = ChatbotService.get_user_sessions(user_id)
        
        # 转换时间格式
        for session in sessions:
            if 'created_at' in session and session['created_at']:
                if hasattr(session['created_at'], 'strftime'):
                    session['created_at'] = session['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if 'updated_at' in session and session['updated_at']:
                if hasattr(session['updated_at'], 'strftime'):
                    session['updated_at'] = session['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chatbot/sessions', methods=['POST'])
@jwt_required()
def create_chat_session():
    """创建新的聊天会话"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        session_name = data.get('sessionName', '新对话')
        
        session_id = ChatbotService.create_session(user_id, session_name)
        return jsonify({
            'success': True,
            'sessionId': session_id,
            'message': '会话创建成功'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chatbot/sessions/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_chat_session(session_id):
    """删除聊天会话"""
    try:
        user_id = int(get_jwt_identity())
        success = ChatbotService.delete_session(session_id, user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '会话删除成功'
            })
        else:
            return jsonify({
                'success': False,
                'message': '无权删除该会话'
            }), 403
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chatbot/sessions/<int:session_id>/messages', methods=['GET'])
@jwt_required()
def get_chat_messages(session_id):
    """获取会话的历史消息"""
    try:
        messages = ChatbotService.get_session_messages(session_id)
        
        # 转换时间格式为MySQL字符串格式
        for msg in messages:
            if 'created_at' in msg and msg['created_at']:
                if hasattr(msg['created_at'], 'strftime'):
                    msg['created_at'] = msg['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'messages': messages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chatbot/chat', methods=['POST'])
@jwt_required()
def chat_with_ai():
    """与AI聊天"""
    try:
        user_id = int(get_jwt_identity())
        data = request.get_json()
        
        session_id = data.get('sessionId')
        message = data.get('message')
        use_knowledge_base = data.get('useKnowledgeBase', True)
        
        if not session_id or not message:
            return jsonify({
                'success': False,
                'message': '缺少必要参数'
            }), 400
        
        result = ChatbotService.chat(user_id, session_id, message, use_knowledge_base)
        
        # 添加防缓存头
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chatbot/materials', methods=['GET'])
@jwt_required()
def search_materials():
    """搜索学习资料"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 10))
        
        materials = ChatbotService.search_learning_materials(query, limit)
        return jsonify({
            'success': True,
            'materials': materials
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 学生花名册管理路由 ====================

@app.route('/api/roster/add-student', methods=['POST'])
@jwt_required()
def add_student_to_roster():
    """教师添加学生到花名册"""
    try:
        # 验证教师身份
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        if claims.get('role') != 'teacher':
            return jsonify({'success': False, 'message': '只有教师才能添加学生信息'}), 403
        
        print("=" * 80)
        print(f"[添加学生] 教师ID: {user_id}")
        print(f"[添加学生] 请求头: {dict(request.headers)}")
        print(f"[添加学生] 表单数据: {dict(request.form)}")
        print(f"[添加学生] 文件列表: {dict(request.files)}")
        
        # 获取表单数据
        student_data = {
            'student_name': request.form.get('studentName'),
            'student_id_number': request.form.get('studentIdNumber'),
            'gender': request.form.get('gender'),
            'class_name': request.form.get('className'),
            'grade': request.form.get('grade'),
            'contact_phone': request.form.get('contactPhone')
        }
        
        print(f"[添加学生] 学生数据: {student_data}")
        
        # 验证必填字段
        if not all([student_data['student_name'], student_data['student_id_number']]):
            print("[添加学生] 验证失败: 姓名或学号为空")
            return jsonify({'success': False, 'message': '学生姓名和学号为必填项'}), 400
        
        # 获取人脸图片
        face_image = request.files.get('faceImage')
        if not face_image:
            print("[添加学生] 验证失败: 未提供人脸图片")
            print(f"[添加学生] request.files.keys(): {list(request.files.keys())}")
            return jsonify({'success': False, 'message': '请上传学生人脸照片'}), 400
        
        print(f"[添加学生] 图片信息: filename={face_image.filename}, content_type={face_image.content_type}")
        
        # 添加到花名册
        result = StudentRosterService.add_student_to_roster(user_id, student_data, face_image)
        
        print(f"[添加学生] 结果: {result}")
        print("=" * 80)
        
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    
    except Exception as e:
        print(f"[添加学生] 异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/roster/my-students', methods=['GET'])
@jwt_required()
def get_my_students():
    """获取教师上传的学生花名册"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        if claims.get('role') != 'teacher':
            return jsonify({'success': False, 'message': '无权访问'}), 403
        
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 20))
        
        result = StudentRosterService.get_teacher_roster(user_id, page, page_size)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/roster/delete-student/<int:roster_id>', methods=['DELETE'])
@jwt_required()
def delete_student(roster_id):
    """删除花名册中的学生"""
    try:
        user_id = int(get_jwt_identity())
        claims = get_jwt()
        if claims.get('role') != 'teacher':
            return jsonify({'success': False, 'message': '无权操作'}), 403
        
        result = StudentRosterService.delete_student_from_roster(roster_id, user_id)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/roster/verify-face', methods=['POST'])
def verify_student_face():
    """学生注册时验证人脸"""
    try:
        student_id_number = request.form.get('studentIdNumber')
        verification_image = request.files.get('faceImage')
        
        if not all([student_id_number, verification_image]):
            return jsonify({'success': False, 'message': '请提供学号和人脸照片'}), 400
        
        result = StudentRosterService.verify_student_face(student_id_number, verification_image)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 人脸识别路由 ====================

@app.route('/api/face/register', methods=['POST'])
@jwt_required()
def register_face():
    """注册/更新用户人脸信息"""
    try:
        user_id = int(get_jwt_identity())
        face_image = request.files.get('faceImage')
        
        if not face_image:
            return jsonify({'success': False, 'message': '请上传人脸照片'}), 400
        
        result = FaceService.register_face(user_id, face_image)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/face/status', methods=['GET'])
@jwt_required()
def get_face_status():
    """获取用户人脸注册状态"""
    try:
        user_id = int(get_jwt_identity())
        has_face = FaceService.has_face_registered(user_id)
        
        return jsonify({
            'success': True,
            'hasFace': has_face
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/face/delete', methods=['DELETE'])
@jwt_required()
def delete_face():
    """删除用户人脸信息"""
    try:
        user_id = int(get_jwt_identity())
        result = FaceService.delete_face(user_id)
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/face/detect-blink', methods=['POST'])
def detect_blink():
    """检测眨眼动作"""
    try:
        from face_service import LivenessDetector
        data = request.get_json()
        frame_data = data.get('frame')
        
        if not frame_data:
            return jsonify({'success': False, 'message': '缺少图像数据'}), 400
        
        result = LivenessDetector.detect_blink(frame_data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/face/detect-head-pose', methods=['POST'])
def detect_head_pose():
    """检测头部姿态"""
    try:
        from face_service import LivenessDetector
        data = request.get_json()
        frame_data = data.get('frame')
        
        if not frame_data:
            return jsonify({'success': False, 'message': '缺少图像数据'}), 400
        
        result = LivenessDetector.detect_head_pose(frame_data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/face-login', methods=['POST'])
def face_login():
    """人脸登录（支持活体检测）"""
    try:
        data = request.get_json()
        
        # 检查是否是带活体检测的请求
        if data and 'faceImage' in data:
            face_image_base64 = data.get('faceImage')
            liveness_data = data.get('livenessData', {})
            
            # 带活体检测的人脸验证
            result = FaceService.verify_face_with_liveness(face_image_base64, liveness_data)
        else:
            # 兼容旧的文件上传方式
            face_image = request.files.get('faceImage')
            if not face_image:
                return jsonify({'success': False, 'message': '请上传人脸照片'}), 400
            result = FaceService.verify_face(face_image)
        
        if not result['success']:
            return jsonify(result), 400
        
        if not result.get('matched'):
            log_sql = """
                INSERT INTO face_login_logs (login_success, login_ip)
                VALUES (FALSE, %s)
            """
            Database.execute_query(log_sql, (request.remote_addr,), commit=True)
            return jsonify(result), 401
        
        # 获取用户信息
        user_id = result['user_id']
        user = UserService.get_user_by_id(user_id)
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        if not user.get('is_active', True):
            return jsonify({'success': False, 'message': '账号已被禁用'}), 401
        
        if not user.get('is_verified', False):
            return jsonify({'success': False, 'message': '请先验证邮箱'}), 401
        
        if user.get('role_name') == 'teacher' and not user.get('is_approved', False):
            return jsonify({'success': False, 'message': '账号待审核'}), 401
        
        permissions = UserService.get_user_permissions(user_id)
        
        additional_claims = {
            'role': user['role_name'],
            'permissions': permissions
        }
        access_token = create_access_token(
            identity=str(user_id),
            additional_claims=additional_claims
        )
        
        log_sql = """
            INSERT INTO face_login_logs (user_id, login_success, similarity_score, login_ip)
            VALUES (%s, TRUE, %s, %s)
        """
        Database.execute_query(log_sql, (user_id, result.get('similarity', 0), request.remote_addr), commit=True)
        
        update_sql = "UPDATE users SET last_login = %s WHERE user_id = %s"
        Database.execute_query(update_sql, (datetime.now(), user_id), commit=True)
        
        return jsonify({
            'success': True,
            'message': '人脸登录成功',
            'token': access_token,
            'similarity': result.get('similarity'),
            'userInfo': {
                'userId': user['user_id'],
                'systemAccount': user['system_account'],
                'email': user['email'],
                'realName': user['real_name'],
                'role': user['role_name'],
                'permissions': permissions,
                'photoUrl': user.get('photo_url'),
                'isApproved': user.get('is_approved', True)
            }
        })
    
    except Exception as e:
        print(f"人脸登录异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

# ==================== 私聊消息路由 ====================

@app.route('/api/messages/conversations', methods=['GET'])
@jwt_required()
def get_conversations():
    """获取用户的所有私聊会话"""
    try:
        user_id = int(get_jwt_identity())
        conversations = MessageService.get_user_conversations(user_id)
        return jsonify({'success': True, 'conversations': conversations})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/messages/conversation/<int:other_user_id>', methods=['GET'])
@jwt_required()
def get_conversation_messages(other_user_id):
    """获取与某用户的聊天记录"""
    try:
        user_id = int(get_jwt_identity())
        page = int(request.args.get('page', 1))
        
        conversation_id = MessageService.get_or_create_conversation(user_id, other_user_id)
        messages = MessageService.get_conversation_messages(conversation_id, user_id, page)
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'messages': messages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/messages/send', methods=['POST'])
@jwt_required()
def send_message():
    """发送消息（支持文件上传）"""
    try:
        user_id = int(get_jwt_identity())
        
        # 尝试从 form 或 json 获取数据
        if request.content_type and 'multipart/form-data' in request.content_type:
            receiver_id = request.form.get('receiver_id')
            message_type = request.form.get('message_type', 'text')
            content = request.form.get('content')
            file = request.files.get('file')
        else:
            data = request.get_json() or {}
            receiver_id = data.get('receiver_id')
            message_type = data.get('message_type', 'text')
            content = data.get('content')
            file = None
        
        print(f"[发送消息] user_id={user_id}, receiver_id={receiver_id}, type={message_type}, has_file={file is not None}")
        
        if not receiver_id:
            return jsonify({'success': False, 'message': '缺少接收者'}), 400
        
        result = MessageService.send_message(user_id, int(receiver_id), message_type, content, file)
        
        if result['success']:
            # 通过 WebSocket 发送实时消息
            from websocket_server import send_to_user
            sent = send_to_user(int(receiver_id), 'new_message', result)
            print(f"[发送消息] WebSocket 通知: {sent}")
            return jsonify(result)
        else:
            print(f"[发送消息] 失败: {result.get('message')}")
            return jsonify(result), 400
    except Exception as e:
        print(f"[发送消息] 异常: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/messages/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """获取未读消息数"""
    try:
        user_id = int(get_jwt_identity())
        count = MessageService.get_unread_count(user_id)
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/messages/search-users', methods=['GET'])
@jwt_required()
def search_users_for_chat():
    """搜索用户"""
    try:
        user_id = int(get_jwt_identity())
        keyword = request.args.get('keyword', '')
        
        if len(keyword) < 1:
            return jsonify({'success': True, 'users': []})
        
        users = MessageService.search_users(keyword, user_id)
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/messages/online-status', methods=['POST'])
@jwt_required()
def get_online_status():
    """获取用户在线状态"""
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        status = MessageService.get_online_status(user_ids)
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# 静态文件服务（消息附件）
@app.route('/uploads/messages/<path:filename>')
def serve_message_file(filename):
    return send_from_directory('uploads/messages', filename)

if __name__ == '__main__':
    import os
    
    if not os.path.exists(Config.UPLOAD_FOLDER):
        os.makedirs(Config.UPLOAD_FOLDER)
    
    # 创建消息上传目录
    os.makedirs('uploads/messages', exist_ok=True)
    
    # 初始化 WebSocket
    init_socketio(app)
    
    print("=" * 50)
    print("服务器启动中...")
    print(f"HTTP API: http://0.0.0.0:5000")
    print(f"WebSocket: ws://0.0.0.0:5000/socket.io")
    print("=" * 50)
    
    # 使用 socketio.run 代替 app.run
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=False,
        log_output=True
    )
