"""
AI聊天机器人服务
集成DeepSeek API，支持基于学习资料库的知识问答
"""

from openai import OpenAI
import os
from config import Config
from database import Database


class ChatbotService:
    """AI聊天机器人服务类"""
    
    @staticmethod
    def search_learning_materials(query, limit=3):
        """
        搜索学习资料库
        增强的关键词匹配搜索，支持优先级
        """
        sql = """
            SELECT material_id, title, content, category, tags, 
                   CASE 
                       WHEN title LIKE %s THEN 3
                       WHEN tags LIKE %s THEN 2
                       WHEN content LIKE %s THEN 1
                       ELSE 0
                   END as relevance_score
            FROM learning_materials 
            WHERE title LIKE %s OR content LIKE %s OR tags LIKE %s
            ORDER BY relevance_score DESC, created_at DESC
            LIMIT %s
        """
        search_pattern = f'%{query}%'
        results = Database.execute_query(
            sql, 
            (search_pattern, search_pattern, search_pattern, 
             search_pattern, search_pattern, search_pattern, limit),
            fetch_all=True
        )
        return results or []
    
    @staticmethod
    def build_context_prompt(user_question, materials, force_knowledge=False):
        """
        构建包含学习资料的提示词
        
        Args:
            user_question: 用户问题
            materials: 匹配的资料列表
            force_knowledge: 是否强制使用知识库回答（高相关度时）
        """
        if not materials:
            return user_question, False
        
        # 检查是否有高相关度的资料（relevance_score >= 3，即标题完全匹配）
        has_high_relevance = any(m.get('relevance_score', 0) >= 3 for m in materials)
        
        if has_high_relevance or force_knowledge:
            # 高相关度：直接使用知识库内容，不让AI随意发挥
            context = "请严格基于以下知识库内容回答，不要添加知识库中没有的信息：\n\n"
            for i, material in enumerate(materials, 1):
                context += f"{i}. {material['title']}\n"
                context += f"   {material['content']}\n\n"
            context += f"\n问题：{user_question}\n"
            context += "请仅使用上述资料回答，如果资料不足以回答问题，请明确说明。"
            return context, True
        else:
            # 低相关度：提供参考资料，但允许AI补充
            context = "以下是可能相关的参考资料：\n\n"
            for i, material in enumerate(materials, 1):
                context += f"{i}. {material['title']}\n"
                context += f"   {material['content']}\n\n"
            context += f"\n参考以上资料回答问题：{user_question}"
            return context, False
    
    @staticmethod
    def call_tongyi_api(messages, api_key=None):
        """
        调用DeepSeek API
        使用OpenAI客户端库
        """
        if not api_key:
            api_key = os.getenv('DASHSCOPE_API_KEY')
        
        if not api_key or api_key == 'your-dashscope-api-key-here':
            # 如果没有配置API Key，返回模拟响应
            return {
                'success': True,
                'message': '（演示模式）你好！我是AI助教。由于未配置API Key，这是一个模拟回复。请配置API Key后使用真实AI功能。\n\n' + 
                          '如何配置：\n1. 获取API Key\n2. 在.env文件中设置 DASHSCOPE_API_KEY',
                'is_demo': True
            }
        
        try:
            # 初始化OpenAI客户端
            client = OpenAI(
                api_key=api_key,
                base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
            )
            
            # 调用DeepSeek API
            completion = client.chat.completions.create(
                model="deepseek-v3.2-exp",
                messages=messages,
                stream=False  # 不使用流式响应以简化处理
            )
            
            if completion.choices and len(completion.choices) > 0:
                ai_message = completion.choices[0].message.content
                return {
                    'success': True,
                    'message': ai_message,
                    'is_demo': False
                }
            else:
                return {
                    'success': False,
                    'message': 'API返回格式错误'
                }
        
        except Exception as e:
            return {
                'success': False,
                'message': f'API调用失败: {str(e)}'
            }
    
    @staticmethod
    def create_session(user_id, session_name='新对话'):
        """创建新的聊天会话"""
        sql = "INSERT INTO chat_sessions (user_id, session_name) VALUES (%s, %s)"
        session_id = Database.execute_query(sql, (user_id, session_name), commit=True)
        return session_id
    
    @staticmethod
    def get_user_sessions(user_id):
        """获取用户的所有会话"""
        sql = """
            SELECT session_id, session_name, created_at, updated_at
            FROM chat_sessions
            WHERE user_id = %s
            ORDER BY updated_at DESC
        """
        sessions = Database.execute_query(sql, (user_id,), fetch_all=True)
        return sessions or []
    
    @staticmethod
    def get_session_messages(session_id, limit=50):
        """获取会话的历史消息"""
        sql = """
            SELECT message_id, role, content, created_at
            FROM chat_messages
            WHERE session_id = %s
            ORDER BY created_at ASC
            LIMIT %s
        """
        messages = Database.execute_query(sql, (session_id, limit), fetch_all=True)
        return messages or []
    
    @staticmethod
    def save_message(session_id, role, content):
        """保存消息到数据库"""
        sql = "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)"
        message_id = Database.execute_query(sql, (session_id, role, content), commit=True)
        
        # 更新会话的updated_at
        update_sql = "UPDATE chat_sessions SET updated_at = CURRENT_TIMESTAMP WHERE session_id = %s"
        Database.execute_query(update_sql, (session_id,), commit=True)
        
        return message_id
    
    @staticmethod
    def delete_session(session_id, user_id):
        """删除会话（需要验证用户权限）"""
        # 先验证会话是否属于该用户
        check_sql = "SELECT user_id FROM chat_sessions WHERE session_id = %s"
        result = Database.execute_query(check_sql, (session_id,), fetch_one=True)
        
        if not result or result['user_id'] != user_id:
            return False
        
        # 删除会话（级联删除消息）
        delete_sql = "DELETE FROM chat_sessions WHERE session_id = %s"
        Database.execute_query(delete_sql, (session_id,), commit=True)
        return True
    
    @staticmethod
    def chat(user_id, session_id, user_message, use_knowledge_base=True):
        """
        处理聊天请求
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            user_message: 用户消息
            use_knowledge_base: 是否使用知识库
        
        Returns:
            dict: 包含AI回复的字典
        """
        # 保存用户消息
        ChatbotService.save_message(session_id, 'user', user_message)
        
        # 获取历史消息（用于上下文）
        history = ChatbotService.get_session_messages(session_id, limit=20)
        
        # 构建消息列表
        messages = []
        
        # 系统提示词
        system_prompt = "你是一个友好、专业的AI助教，负责帮助学生学习。请用简洁、易懂的语言回答问题。"
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # 如果启用知识库，搜索相关资料
        context_message = user_message
        used_knowledge_base = False
        if use_knowledge_base:
            materials = ChatbotService.search_learning_materials(user_message)
            if materials:
                context_message, used_knowledge_base = ChatbotService.build_context_prompt(user_message, materials)
        
        # 添加历史消息（最近的几条）
        for msg in history[:-1]:  # 排除刚保存的用户消息
            messages.append({
                "role": msg['role'],
                "content": msg['content']
            })
        
        # 添加当前用户消息
        messages.append({
            "role": "user",
            "content": context_message
        })
        
        # 调用AI API
        result = ChatbotService.call_tongyi_api(messages)
        
        if result['success']:
            # 保存AI回复
            ChatbotService.save_message(session_id, 'assistant', result['message'])
            return {
                'success': True,
                'message': result['message'],
                'is_demo': result.get('is_demo', False)
            }
        else:
            return {
                'success': False,
                'message': result['message']
            }
    
    @staticmethod
    def get_all_materials(category=None, page=1, page_size=20):
        """
        获取所有学习资料（分页）
        """
        offset = (page - 1) * page_size
        
        if category:
            sql = """
                SELECT m.*, u.real_name as creator_name
                FROM learning_materials m
                LEFT JOIN users u ON m.created_by = u.user_id
                WHERE m.category = %s
                ORDER BY m.created_at DESC
                LIMIT %s OFFSET %s
            """
            materials = Database.execute_query(sql, (category, page_size, offset), fetch_all=True)
            
            count_sql = "SELECT COUNT(*) as total FROM learning_materials WHERE category = %s"
            count_result = Database.execute_query(count_sql, (category,), fetch_one=True)
        else:
            sql = """
                SELECT m.*, u.real_name as creator_name
                FROM learning_materials m
                LEFT JOIN users u ON m.created_by = u.user_id
                ORDER BY m.created_at DESC
                LIMIT %s OFFSET %s
            """
            materials = Database.execute_query(sql, (page_size, offset), fetch_all=True)
            
            count_sql = "SELECT COUNT(*) as total FROM learning_materials"
            count_result = Database.execute_query(count_sql, fetch_one=True)
        
        total = count_result['total'] if count_result else 0
        
        return {
            'materials': materials or [],
            'total': total,
            'page': page,
            'page_size': page_size
        }
    
    @staticmethod
    def add_material(title, content, category, tags, created_by):
        """
        添加学习资料
        """
        sql = """
            INSERT INTO learning_materials (title, content, category, tags, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            material_id = Database.execute_query(
                sql, 
                (title, content, category, tags, created_by),
                commit=True
            )
            return {'success': True, 'material_id': material_id, 'message': '资料添加成功'}
        except Exception as e:
            return {'success': False, 'message': f'添加失败: {str(e)}'}
    
    @staticmethod
    def update_material(material_id, title, content, category, tags):
        """
        更新学习资料
        """
        sql = """
            UPDATE learning_materials 
            SET title = %s, content = %s, category = %s, tags = %s
            WHERE material_id = %s
        """
        try:
            Database.execute_query(
                sql,
                (title, content, category, tags, material_id),
                commit=True
            )
            return {'success': True, 'message': '资料更新成功'}
        except Exception as e:
            return {'success': False, 'message': f'更新失败: {str(e)}'}
    
    @staticmethod
    def delete_material(material_id):
        """
        删除学习资料
        """
        sql = "DELETE FROM learning_materials WHERE material_id = %s"
        try:
            Database.execute_query(sql, (material_id,), commit=True)
            return {'success': True, 'message': '资料删除成功'}
        except Exception as e:
            return {'success': False, 'message': f'删除失败: {str(e)}'}
    
    @staticmethod
    def get_material_by_id(material_id):
        """
        根据ID获取资料详情
        """
        sql = """
            SELECT m.*, u.real_name as creator_name
            FROM learning_materials m
            LEFT JOIN users u ON m.created_by = u.user_id
            WHERE m.material_id = %s
        """
        return Database.execute_query(sql, (material_id,), fetch_one=True)
    
    @staticmethod
    def get_categories():
        """
        获取所有分类
        """
        sql = "SELECT DISTINCT category FROM learning_materials WHERE category IS NOT NULL ORDER BY category"
        results = Database.execute_query(sql, fetch_all=True)
        return [r['category'] for r in results] if results else []
