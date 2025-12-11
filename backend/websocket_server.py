"""
WebSocket 服务器
使用 Flask-SocketIO 实现实时通信
"""
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import decode_token
from flask import request
from message_service import MessageService

socketio = SocketIO()

# 存储用户连接信息 {user_id: sid}
connected_users = {}


def init_socketio(app):
    """初始化 SocketIO - 使用 gevent 作为异步后端"""
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='gevent',
        ping_timeout=60,
        ping_interval=25
    )
    print("WebSocket 服务器初始化完成 (async_mode=gevent)")
    return socketio


@socketio.on('connect')
def handle_connect(auth=None):
    """处理连接"""
    sid = request.sid
    print(f'[WebSocket] 客户端连接: {sid}')
    print(f'[WebSocket] 当前连接数: {len(connected_users)}')


@socketio.on('authenticate')
def handle_authenticate(data):
    """用户认证"""
    try:
        token = data.get('token')
        if not token:
            print('[WebSocket] 认证失败: 缺少token')
            emit('auth_error', {'message': '缺少token'})
            return

        # 解析 JWT token
        decoded = decode_token(token)
        user_id = int(decoded['sub'])
        sid = request.sid

        # 保存用户连接
        connected_users[user_id] = sid

        # 加入个人房间 - 这是接收消息和通话的关键
        room_name = f'user_{user_id}'
        join_room(room_name)
        print(f'[WebSocket] 用户 {user_id} 加入房间: {room_name}')

        # 更新在线状态
        MessageService.update_online_status(user_id, True, sid)

        # 通知好友上线
        broadcast_online_status(user_id, True)

        emit('authenticated', {'user_id': user_id})
        print(f'[WebSocket] 用户 {user_id} 认证成功, sid: {sid}')
        print(f'[WebSocket] 当前在线用户: {list(connected_users.keys())}')

    except Exception as e:
        print(f'[WebSocket] 认证失败: {e}')
        import traceback
        traceback.print_exc()
        emit('auth_error', {'message': str(e)})


@socketio.on('disconnect')
def handle_disconnect():
    """处理断开连接"""
    sid = request.sid

    # 查找断开的用户
    user_id = None
    for uid, s in list(connected_users.items()):
        if s == sid:
            user_id = uid
            del connected_users[uid]
            break

    if user_id:
        # 更新在线状态
        MessageService.update_online_status(user_id, False)

        # 通知好友下线
        broadcast_online_status(user_id, False)

        print(f'用户 {user_id} 断开连接')


def get_user_id_from_sid(sid):
    """根据 sid 获取用户 ID"""
    for uid, s in connected_users.items():
        if s == sid:
            return uid
    return None


@socketio.on('send_message')
def handle_send_message(data):
    """处理发送消息"""
    try:
        sid = request.sid
        sender_id = get_user_id_from_sid(sid)

        if not sender_id:
            emit('error', {'message': '未认证'})
            return

        receiver_id = data.get('receiver_id')
        message_type = data.get('message_type', 'text')
        content = data.get('content')

        if not receiver_id:
            emit('error', {'message': '缺少接收者'})
            return

        print(f'[消息] 发送: {sender_id} -> {receiver_id}, 类型: {message_type}')

        # 保存消息到数据库
        result = MessageService.send_message(sender_id, int(receiver_id), message_type, content)

        if result['success']:
            message_data = {
                'message_id': result['message_id'],
                'conversation_id': result['conversation_id'],
                'sender_id': sender_id,
                'receiver_id': int(receiver_id),
                'message_type': message_type,
                'content': content,
                'file_url': result.get('file_url'),
                'file_name': result.get('file_name'),
                'file_size': result.get('file_size'),
                'sender_name': result['sender_name'],
                'sender_avatar': result['sender_avatar'],
                'created_at': result['created_at'],
                'is_read': False
            }

            # 发送给接收者 - 使用 socketio.emit 确保发送到正确的房间
            target_room = f'user_{receiver_id}'
            socketio.emit('new_message', message_data, room=target_room)

            # 确认发送成功
            emit('message_sent', message_data)
            print(f'[消息] 发送成功: {sender_id} -> {receiver_id}')
        else:
            emit('error', {'message': result.get('message', '发送失败')})

    except Exception as e:
        print(f'[消息] 发送错误: {e}')
        import traceback
        traceback.print_exc()
        emit('error', {'message': str(e)})


@socketio.on('typing')
def handle_typing(data):
    """处理正在输入状态"""
    sid = request.sid
    sender_id = get_user_id_from_sid(sid)

    if sender_id:
        receiver_id = data.get('receiver_id')
        is_typing = data.get('is_typing', False)

        emit('user_typing', {
            'user_id': sender_id,
            'is_typing': is_typing
        }, room=f'user_{receiver_id}')


@socketio.on('mark_read')
def handle_mark_read(data):
    """标记消息已读"""
    conversation_id = data.get('conversation_id')
    sid = request.sid
    user_id = get_user_id_from_sid(sid)

    if user_id and conversation_id:
        # 更新数据库
        from database import Database
        sql = """
            UPDATE private_messages 
            SET is_read = TRUE 
            WHERE conversation_id = %s AND receiver_id = %s AND is_read = FALSE
        """
        Database.execute_query(sql, (conversation_id, user_id), commit=True)

        # 通知发送者消息已读
        sender_id = data.get('sender_id')
        if sender_id:
            emit('messages_read', {
                'conversation_id': conversation_id,
                'reader_id': user_id
            }, room=f'user_{sender_id}')


# ==================== WebRTC 视频通话信令 ====================

# 存储当前通话信息 {caller_id: {receiver_id, is_video, start_time}}
active_calls = {}


def save_call_record(caller_id, receiver_id, is_video, status, duration=0):
    """保存通话记录到消息表"""
    try:
        call_type = 'video_call' if is_video else 'voice_call'
        # 通话内容：状态和时长
        if status == 'completed':
            content = f"通话时长: {duration}秒"
        elif status == 'rejected':
            content = "对方已拒绝"
        elif status == 'missed':
            content = "未接听"
        elif status == 'cancelled':
            content = "已取消"
        else:
            content = status
        
        # 保存消息
        result = MessageService.send_message(caller_id, receiver_id, call_type, content)
        print(f"[通话记录] 保存成功: {caller_id} -> {receiver_id}, {call_type}, {content}")
        return result
    except Exception as e:
        print(f"[通话记录] 保存失败: {e}")
        return None


@socketio.on('call_user')
def handle_call_user(data):
    """发起视频/语音通话"""
    sid = request.sid
    caller_id = get_user_id_from_sid(sid)

    if not caller_id:
        print('[通话] 错误: 呼叫者未认证')
        emit('error', {'message': '未认证'})
        return

    receiver_id = data.get('receiver_id')
    signal = data.get('signal')
    is_video = data.get('is_video', True)

    print(f'[通话] ========== 发起通话 ==========')
    print(f'[通话] 呼叫者: {caller_id} -> 接收者: {receiver_id}')
    print(f'[通话] 类型: {"视频" if is_video else "语音"}')
    print(f'[通话] 当前在线用户: {list(connected_users.keys())}')
    print(f'[通话] 接收者 {receiver_id} 在线: {int(receiver_id) in connected_users}')

    # 检查接收者是否在线
    if int(receiver_id) not in connected_users:
        print(f'[通话] 失败: 接收者 {receiver_id} 不在线')
        # 保存未接来电记录
        save_call_record(caller_id, int(receiver_id), is_video, 'missed')
        emit('call_rejected', {'reason': '对方不在线'})
        return

    # 获取呼叫者信息
    from database import Database
    sql = "SELECT real_name, photo_url FROM users WHERE user_id = %s"
    caller = Database.execute_query(sql, (caller_id,), fetch_one=True)

    if not caller:
        print('[通话] 错误: 获取呼叫者信息失败')
        emit('error', {'message': '用户信息获取失败'})
        return

    # 记录通话开始
    import time
    active_calls[caller_id] = {
        'receiver_id': int(receiver_id),
        'is_video': is_video,
        'start_time': time.time()
    }

    # 发送来电通知给接收者
    call_data = {
        'caller_id': caller_id,
        'caller_name': caller['real_name'],
        'caller_avatar': caller['photo_url'],
        'signal': signal,
        'is_video': is_video
    }
    
    # 确保不会发送给发起者自己
    if caller_id == int(receiver_id):
        print(f'[通话] 错误: 不能呼叫自己')
        emit('call_rejected', {'reason': '不能呼叫自己'})
        return
    
    target_room = f'user_{receiver_id}'
    print(f'[通话] 发送 incoming_call 事件到房间: {target_room}')
    print(f'[通话] 通话数据: caller_id={caller_id}, caller_name={caller["real_name"]}')
    
    # 使用 socketio.emit 而不是 emit，确保发送到正确的房间
    socketio.emit('incoming_call', call_data, room=target_room)
    print(f'[通话] 来电通知已发送')
    print(f'[通话] ================================')


@socketio.on('answer_call')
def handle_answer_call(data):
    """接听视频通话"""
    sid = request.sid
    answerer_id = get_user_id_from_sid(sid)
    caller_id = data.get('caller_id')
    signal = data.get('signal')

    print(f'[通话] 接听: 用户 {answerer_id} 接听 用户 {caller_id} 的通话')
    
    # 更新通话开始时间（从接听时开始计算）
    if caller_id in active_calls:
        import time
        active_calls[caller_id]['start_time'] = time.time()
        active_calls[caller_id]['answered'] = True
    
    target_room = f'user_{caller_id}'
    print(f'[通话] 发送 call_answered 到房间: {target_room}')
    socketio.emit('call_answered', {'signal': signal}, room=target_room)


@socketio.on('reject_call')
def handle_reject_call(data):
    """拒绝视频通话"""
    sid = request.sid
    rejecter_id = get_user_id_from_sid(sid)
    caller_id = data.get('caller_id')
    
    print(f'[通话] 拒绝: 用户 {rejecter_id} 拒绝 用户 {caller_id} 的通话')
    
    # 保存拒绝记录
    if caller_id in active_calls:
        call_info = active_calls.pop(caller_id)
        save_call_record(caller_id, call_info['receiver_id'], call_info['is_video'], 'rejected')
    
    target_room = f'user_{caller_id}'
    print(f'[通话] 发送 call_rejected 到房间: {target_room}')
    socketio.emit('call_rejected', {'reason': '对方拒绝了通话'}, room=target_room)


@socketio.on('end_call')
def handle_end_call(data):
    """结束视频通话"""
    sid = request.sid
    user_id = get_user_id_from_sid(sid)
    other_user_id = data.get('other_user_id')
    
    print(f'[通话] 结束: 用户 {user_id} 结束与 用户 {other_user_id} 的通话')
    
    # 计算通话时长并保存记录
    import time
    call_info = None
    
    # 检查是否是呼叫者结束
    if user_id in active_calls:
        call_info = active_calls.pop(user_id)
    # 检查是否是接听者结束
    else:
        for cid, info in list(active_calls.items()):
            if info['receiver_id'] == user_id:
                call_info = active_calls.pop(cid)
                break
    
    if call_info:
        if call_info.get('answered'):
            # 已接听的通话，计算时长
            duration = int(time.time() - call_info['start_time'])
            save_call_record(user_id, int(other_user_id), call_info['is_video'], 'completed', duration)
        else:
            # 未接听就取消
            save_call_record(user_id, int(other_user_id), call_info['is_video'], 'cancelled')
    
    if other_user_id:
        target_room = f'user_{other_user_id}'
        print(f'[通话] 发送 call_ended 到房间: {target_room}')
        socketio.emit('call_ended', {}, room=target_room)


@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    """处理 ICE candidate"""
    other_user_id = data.get('other_user_id')
    candidate = data.get('candidate')

    if other_user_id:
        target_room = f'user_{other_user_id}'
        socketio.emit('ice_candidate', {'candidate': candidate}, room=target_room)


# ==================== 辅助函数 ====================

def broadcast_online_status(user_id, is_online):
    """广播用户在线状态"""
    try:
        conversations = MessageService.get_user_conversations(user_id)
        print(f'[在线状态] 用户 {user_id} {"上线" if is_online else "下线"}, 通知 {len(conversations)} 个会话')

        for conv in conversations:
            other_user_id = conv['other_user_id']
            if other_user_id in connected_users:
                target_room = f'user_{other_user_id}'
                socketio.emit('user_status_changed', {
                    'user_id': user_id,
                    'is_online': is_online
                }, room=target_room)
    except Exception as e:
        print(f'[在线状态] 广播错误: {e}')


def send_to_user(user_id, event, data):
    """发送消息给指定用户"""
    if user_id in connected_users:
        socketio.emit(event, data, room=f'user_{user_id}')
        return True
    return False


def get_online_users():
    """获取所有在线用户"""
    return list(connected_users.keys())


# ==================== 群聊 WebSocket 事件 ====================

@socketio.on('join_group')
def handle_join_group(data):
    """加入群聊房间"""
    sid = request.sid
    user_id = get_user_id_from_sid(sid)
    group_id = data.get('group_id')
    
    if not user_id or not group_id:
        return
    
    # 验证用户是否是群成员
    from database import Database
    sql = "SELECT id FROM group_members WHERE group_id = %s AND user_id = %s"
    member = Database.execute_query(sql, (group_id, user_id), fetch_one=True)
    
    if member:
        room_name = f'group_{group_id}'
        join_room(room_name)
        print(f'[群聊] 用户 {user_id} 加入群聊房间: {room_name}')
        emit('joined_group', {'group_id': group_id})


@socketio.on('leave_group_room')
def handle_leave_group_room(data):
    """离开群聊房间"""
    group_id = data.get('group_id')
    if group_id:
        room_name = f'group_{group_id}'
        leave_room(room_name)
        print(f'[群聊] 用户离开群聊房间: {room_name}')


@socketio.on('send_group_message')
def handle_send_group_message(data):
    """发送群消息"""
    sid = request.sid
    sender_id = get_user_id_from_sid(sid)
    
    if not sender_id:
        emit('error', {'message': '未认证'})
        return
    
    group_id = data.get('group_id')
    message_type = data.get('message_type', 'text')
    content = data.get('content')
    
    if not group_id or not content:
        emit('error', {'message': '缺少必要参数'})
        return
    
    from database import Database
    from datetime import datetime, timedelta
    import hashlib
    import uuid
    
    # 验证用户是否是群成员
    sql = "SELECT role, is_muted FROM group_members WHERE group_id = %s AND user_id = %s"
    member = Database.execute_query(sql, (group_id, sender_id), fetch_one=True)
    
    if not member:
        emit('error', {'message': '您不是该群成员'})
        return
    
    if member['is_muted']:
        emit('error', {'message': '您已被禁言'})
        return
    
    checkin_id = None
    checkin_code = None
    
    # 如果是签到消息，先创建签到记录
    if message_type == 'checkin':
        # 验证是否是管理员或群主
        if member['role'] not in ('owner', 'admin'):
            emit('error', {'message': '只有群主或管理员可以发起签到'})
            return
        
        checkin_type = data.get('checkin_type', 'qrcode')
        duration = data.get('duration', 5)
        gesture_number = data.get('gesture_number')
        location_lat = data.get('location_lat')
        location_lng = data.get('location_lng')
        location_range = data.get('location_range', 50)
        
        # 生成签到码
        checkin_code = hashlib.md5(f"{uuid.uuid4()}{datetime.now().timestamp()}".encode()).hexdigest()[:8].upper()
        end_time = datetime.now() + timedelta(minutes=duration)
        
        # 创建签到记录
        sql = """
            INSERT INTO checkins (group_id, creator_id, title, type, checkin_code, 
                                  duration, end_time, description, gesture_number,
                                  location_lat, location_lng, location_range, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'active')
        """
        checkin_id = Database.execute_query(sql, (
            group_id, sender_id, content, checkin_type, checkin_code,
            duration, end_time, '', gesture_number,
            location_lat, location_lng, location_range
        ), commit=True)
        
        print(f'[群聊签到] 创建签到: ID={checkin_id}, 类型={checkin_type}, 时长={duration}分钟')
    
    # 保存消息
    if checkin_id:
        sql = """
            INSERT INTO group_messages (group_id, sender_id, message_type, content, reference_id, reference_type)
            VALUES (%s, %s, %s, %s, %s, 'checkin')
        """
        message_id = Database.execute_query(sql, (group_id, sender_id, message_type, content, checkin_id), commit=True)
    else:
        sql = """
            INSERT INTO group_messages (group_id, sender_id, message_type, content)
            VALUES (%s, %s, %s, %s)
        """
        message_id = Database.execute_query(sql, (group_id, sender_id, message_type, content), commit=True)
    
    # 获取发送者信息
    sql = "SELECT real_name, photo_url FROM users WHERE user_id = %s"
    sender = Database.execute_query(sql, (sender_id,), fetch_one=True)
    
    # 获取消息时间
    sql = "SELECT created_at FROM group_messages WHERE id = %s"
    msg = Database.execute_query(sql, (message_id,), fetch_one=True)
    
    message_data = {
        'id': message_id,
        'group_id': group_id,
        'sender_id': sender_id,
        'sender_name': sender['real_name'],
        'sender_avatar': sender['photo_url'],
        'message_type': message_type,
        'content': content,
        'created_at': msg['created_at'].isoformat() if msg else None,
        'reference_id': checkin_id,
        'checkin_code': checkin_code
    }
    
    # 广播到群聊房间
    room_name = f'group_{group_id}'
    socketio.emit('new_group_message', message_data, room=room_name)
    print(f'[群聊] 消息发送: 用户 {sender_id} -> 群 {group_id}')


def broadcast_to_group(group_id, event, data, exclude_user=None):
    """广播消息到群组所有成员"""
    room_name = f'group_{group_id}'
    socketio.emit(event, data, room=room_name)


def notify_group_members(group_id, event, data):
    """通知群组成员（即使不在群聊房间）"""
    from database import Database
    sql = "SELECT user_id FROM group_members WHERE group_id = %s"
    members = Database.execute_query(sql, (group_id,), fetch_all=True)
    
    for member in members:
        user_id = member['user_id']
        if user_id in connected_users:
            socketio.emit(event, data, room=f'user_{user_id}')
