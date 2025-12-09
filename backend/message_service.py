"""
私聊消息服务
"""
import os
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from database import Database
from config import Config

class MessageService:
    """私聊消息服务"""
    
    UPLOAD_FOLDER = 'uploads/messages'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'mp4', 'webm', 'mp3', 'wav', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'zip', 'rar'}
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    
    @staticmethod
    def init_folders():
        os.makedirs(MessageService.UPLOAD_FOLDER, exist_ok=True)
    
    @staticmethod
    def allowed_file(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in MessageService.ALLOWED_EXTENSIONS
    
    @staticmethod
    def get_or_create_conversation(user1_id, user2_id):
        """获取或创建私聊会话"""
        # 确保 user1_id < user2_id，保证唯一性
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        # 查找现有会话
        sql = """
            SELECT conversation_id FROM private_conversations 
            WHERE user1_id = %s AND user2_id = %s
        """
        result = Database.execute_query(sql, (user1_id, user2_id), fetch_one=True)
        
        if result:
            return result['conversation_id']
        
        # 创建新会话
        insert_sql = """
            INSERT INTO private_conversations (user1_id, user2_id) VALUES (%s, %s)
        """
        Database.execute_query(insert_sql, (user1_id, user2_id), commit=True)
        
        # 获取新创建的会话ID
        result = Database.execute_query(sql, (user1_id, user2_id), fetch_one=True)
        return result['conversation_id']
    
    @staticmethod
    def get_user_conversations(user_id):
        """获取用户的所有私聊会话"""
        sql = """
            SELECT 
                pc.conversation_id,
                pc.updated_at,
                CASE 
                    WHEN pc.user1_id = %s THEN pc.user2_id 
                    ELSE pc.user1_id 
                END as other_user_id,
                u.real_name as other_user_name,
                u.system_account as other_user_account,
                u.photo_url as other_user_avatar,
                (SELECT content FROM private_messages WHERE conversation_id = pc.conversation_id ORDER BY created_at DESC LIMIT 1) as last_message,
                (SELECT message_type FROM private_messages WHERE conversation_id = pc.conversation_id ORDER BY created_at DESC LIMIT 1) as last_message_type,
                (SELECT created_at FROM private_messages WHERE conversation_id = pc.conversation_id ORDER BY created_at DESC LIMIT 1) as last_message_time,
                (SELECT COUNT(*) FROM private_messages WHERE conversation_id = pc.conversation_id AND receiver_id = %s AND is_read = FALSE) as unread_count
            FROM private_conversations pc
            JOIN users u ON u.user_id = CASE WHEN pc.user1_id = %s THEN pc.user2_id ELSE pc.user1_id END
            WHERE pc.user1_id = %s OR pc.user2_id = %s
            ORDER BY pc.updated_at DESC
        """
        conversations = Database.execute_query(sql, (user_id, user_id, user_id, user_id, user_id), fetch_all=True)
        
        for conv in conversations:
            if conv['last_message_time']:
                conv['last_message_time'] = conv['last_message_time'].strftime('%Y-%m-%d %H:%M:%S')
            if conv['updated_at']:
                conv['updated_at'] = conv['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return conversations
    
    @staticmethod
    def get_conversation_messages(conversation_id, user_id, page=1, page_size=50):
        """获取会话消息"""
        offset = (page - 1) * page_size
        
        sql = """
            SELECT 
                pm.message_id,
                pm.sender_id,
                pm.receiver_id,
                pm.message_type,
                pm.content,
                pm.file_url,
                pm.file_name,
                pm.file_size,
                pm.is_read,
                pm.created_at,
                u.real_name as sender_name,
                u.photo_url as sender_avatar
            FROM private_messages pm
            JOIN users u ON u.user_id = pm.sender_id
            WHERE pm.conversation_id = %s
            ORDER BY pm.created_at DESC
            LIMIT %s OFFSET %s
        """
        messages = Database.execute_query(sql, (conversation_id, page_size, offset), fetch_all=True)
        
        for msg in messages:
            if msg['created_at']:
                msg['created_at'] = msg['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        # 标记消息为已读
        update_sql = """
            UPDATE private_messages 
            SET is_read = TRUE 
            WHERE conversation_id = %s AND receiver_id = %s AND is_read = FALSE
        """
        Database.execute_query(update_sql, (conversation_id, user_id), commit=True)
        
        return list(reversed(messages))
    
    @staticmethod
    def send_message(sender_id, receiver_id, message_type, content=None, file=None):
        """发送消息"""
        conversation_id = MessageService.get_or_create_conversation(sender_id, receiver_id)
        
        file_url = None
        file_name = None
        file_size = None
        
        # 处理文件上传
        if file and message_type in ['image', 'file', 'video', 'voice']:
            MessageService.init_folders()
            
            if not MessageService.allowed_file(file.filename):
                return {'success': False, 'message': '不支持的文件类型'}
            
            filename = secure_filename(f"{sender_id}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{file.filename}")
            filepath = os.path.join(MessageService.UPLOAD_FOLDER, filename)
            file.save(filepath)
            
            file_url = f'/uploads/messages/{filename}'
            file_name = file.filename
            file_size = os.path.getsize(filepath)
        
        # 插入消息
        insert_sql = """
            INSERT INTO private_messages 
            (conversation_id, sender_id, receiver_id, message_type, content, file_url, file_name, file_size)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        Database.execute_query(insert_sql, (
            conversation_id, sender_id, receiver_id, message_type, 
            content, file_url, file_name, file_size
        ), commit=True)
        
        # 更新会话时间
        update_sql = "UPDATE private_conversations SET updated_at = NOW() WHERE conversation_id = %s"
        Database.execute_query(update_sql, (conversation_id,), commit=True)
        
        # 获取发送者信息
        sender_sql = "SELECT real_name, photo_url FROM users WHERE user_id = %s"
        sender = Database.execute_query(sender_sql, (sender_id,), fetch_one=True)
        
        # 获取新消息ID
        msg_sql = "SELECT LAST_INSERT_ID() as message_id"
        msg_result = Database.execute_query(msg_sql, fetch_one=True)
        
        return {
            'success': True,
            'message_id': msg_result['message_id'],
            'conversation_id': conversation_id,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'message_type': message_type,
            'content': content,
            'file_url': file_url,
            'file_name': file_name,
            'file_size': file_size,
            'sender_name': sender['real_name'],
            'sender_avatar': sender['photo_url'],
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def get_unread_count(user_id):
        """获取未读消息总数"""
        sql = "SELECT COUNT(*) as count FROM private_messages WHERE receiver_id = %s AND is_read = FALSE"
        result = Database.execute_query(sql, (user_id,), fetch_one=True)
        return result['count'] if result else 0
    
    @staticmethod
    def search_users(keyword, current_user_id):
        """搜索用户"""
        sql = """
            SELECT user_id, real_name, system_account, photo_url, r.role_name
            FROM users u
            JOIN roles r ON u.role_id = r.role_id
            WHERE u.user_id != %s 
            AND u.is_active = TRUE 
            AND (u.real_name LIKE %s OR u.system_account LIKE %s)
            LIMIT 20
        """
        keyword_pattern = f'%{keyword}%'
        return Database.execute_query(sql, (current_user_id, keyword_pattern, keyword_pattern), fetch_all=True)
    
    @staticmethod
    def update_online_status(user_id, is_online, socket_id=None):
        """更新用户在线状态"""
        sql = """
            INSERT INTO user_online_status (user_id, is_online, socket_id)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE is_online = %s, socket_id = %s, last_seen = NOW()
        """
        Database.execute_query(sql, (user_id, is_online, socket_id, is_online, socket_id), commit=True)
    
    @staticmethod
    def get_online_status(user_ids):
        """获取用户在线状态"""
        if not user_ids:
            return {}
        
        placeholders = ','.join(['%s'] * len(user_ids))
        sql = f"SELECT user_id, is_online, last_seen FROM user_online_status WHERE user_id IN ({placeholders})"
        results = Database.execute_query(sql, tuple(user_ids), fetch_all=True)
        
        status_map = {}
        for r in results:
            status_map[r['user_id']] = {
                'is_online': r['is_online'],
                'last_seen': r['last_seen'].strftime('%Y-%m-%d %H:%M:%S') if r['last_seen'] else None
            }
        return status_map
