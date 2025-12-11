# -*- coding: utf-8 -*-
"""更新签到表，添加智能点到(photo)类型"""
from database import Database

def update_schema():
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    try:
        # 修改 type 枚举，添加 photo
        cursor.execute("""
            ALTER TABLE checkins 
            MODIFY COLUMN type ENUM('normal', 'qrcode', 'location', 'question', 'face', 'gesture', 'photo') DEFAULT 'qrcode'
        """)
        print("✓ 已添加 photo 签到类型")
        
        conn.commit()
        print("\n数据库更新成功！")
    except Exception as e:
        print(f"更新失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    update_schema()
