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
        简单的关键词匹配搜索
        """
        sql = """
            SELECT title, content, category, tags 
            FROM learning_materials 
            WHERE title LIKE %s OR content LIKE %s OR tags LIKE %s
            LIMIT %s
        """
        search_pattern = f'%{query}%'
        results = Database.execute_query(
            sql, 
            (search_pattern, search_pattern, search_pattern, limit),
            fetch_all=True
        )
        return results or []
    
    @staticmethod
    def build_context_prompt(user_question, materials):
        """
        构建包含学习资料的提示词
        """
        if not materials:
            return user_question
        
        context = "以下是相关的学习资料：\n\n"
        for i, material in enumerate(materials, 1):
            context += f"{i}. {material['title']}\n"
            context += f"   {material['content']}\n\n"
        
        context += f"基于以上学习资料，请回答：{user_question}"
        return context
    
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
        if use_knowledge_base:
            materials = ChatbotService.search_learning_materials(user_message)
            if materials:
                context_message = ChatbotService.build_context_prompt(user_message, materials)
        
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
