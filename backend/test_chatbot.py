"""
快速测试脚本 - 验证AI聊天机器人功能
"""

from chatbot_service import ChatbotService

def test_chatbot():
    print("=" * 50)
    print("测试AI聊天机器人功能")
    print("=" * 50)
    
    # 测试1: 创建会话
    print("\n[测试1] 创建会话...")
    try:
        session_id = ChatbotService.create_session(1, "测试会话")
        print(f"✅ 会话创建成功! Session ID: {session_id}")
    except Exception as e:
        print(f"❌ 创建会话失败: {e}")
        return
    
    # 测试2: 获取会话列表
    print("\n[测试2] 获取会话列表...")
    try:
        sessions = ChatbotService.get_user_sessions(1)
        print(f"✅ 找到 {len(sessions)} 个会话")
        for session in sessions:
            print(f"   - {session['session_name']} (ID: {session['session_id']})")
    except Exception as e:
        print(f"❌ 获取会话列表失败: {e}")
    
    # 测试3: 搜索学习资料
    print("\n[测试3] 搜索学习资料...")
    try:
        materials = ChatbotService.search_learning_materials("Python")
        print(f"✅ 找到 {len(materials)} 个相关资料")
        for material in materials:
            print(f"   - {material['title']}")
    except Exception as e:
        print(f"❌ 搜索资料失败: {e}")
    
    # 测试4: 保存消息
    print("\n[测试4] 保存消息...")
    try:
        msg_id1 = ChatbotService.save_message(session_id, "user", "什么是Python?")
        msg_id2 = ChatbotService.save_message(session_id, "assistant", "Python是一种编程语言...")
        print(f"✅ 消息保存成功! Message IDs: {msg_id1}, {msg_id2}")
    except Exception as e:
        print(f"❌ 保存消息失败: {e}")
    
    # 测试5: 获取历史消息
    print("\n[测试5] 获取历史消息...")
    try:
        messages = ChatbotService.get_session_messages(session_id)
        print(f"✅ 找到 {len(messages)} 条消息")
        for msg in messages:
            print(f"   [{msg['role']}] {msg['content'][:30]}...")
    except Exception as e:
        print(f"❌ 获取消息失败: {e}")
    
    # 测试6: AI聊天(演示模式)
    print("\n[测试6] AI聊天(演示模式)...")
    try:
        result = ChatbotService.chat(1, session_id, "什么是Vue3?", use_knowledge_base=True)
        if result['success']:
            print(f"✅ AI回复成功!")
            print(f"   回复内容: {result['message'][:100]}...")
            if result.get('is_demo'):
                print(f"   💡 当前为演示模式,配置API Key后可使用真实AI")
        else:
            print(f"❌ AI回复失败: {result['message']}")
    except Exception as e:
        print(f"❌ AI聊天失败: {e}")
    
    # 测试7: 删除会话
    print("\n[测试7] 删除会话...")
    try:
        success = ChatbotService.delete_session(session_id, 1)
        if success:
            print(f"✅ 会话删除成功!")
        else:
            print(f"❌ 会话删除失败(权限不足)")
    except Exception as e:
        print(f"❌ 删除会话失败: {e}")
    
    print("\n" + "=" * 50)
    print("所有测试完成!")
    print("=" * 50)

if __name__ == '__main__':
    test_chatbot()
