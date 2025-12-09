"""
更新消息表 schema，添加 video_call 和 voice_call 类型
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from database import Database

def update_schema():
    """更新 private_messages 表的 message_type 枚举"""
    try:
        # 修改 message_type 枚举，添加 video_call 和 voice_call
        sql = """
            ALTER TABLE private_messages 
            MODIFY COLUMN message_type 
            ENUM('text', 'image', 'file', 'video', 'emoji', 'voice', 'video_call', 'voice_call') 
            DEFAULT 'text'
        """
        Database.execute_query(sql, commit=True)
        print("[OK] message_type updated with video_call and voice_call")
        return True
    except Exception as e:
        print(f"[ERROR] Update failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("Updating message schema...")
    update_schema()
    print("Done.")
