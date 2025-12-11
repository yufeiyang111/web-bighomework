# -*- coding: utf-8 -*-
"""更新签到表，添加手势签到支持"""
from database import Database

def update_schema():
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    try:
        # 修改 type 枚举，添加 gesture
        cursor.execute("""
            ALTER TABLE checkins 
            MODIFY COLUMN type ENUM('normal', 'qrcode', 'location', 'question', 'face', 'gesture') DEFAULT 'qrcode'
        """)
        print("✓ 已添加 gesture 签到类型")
        
        # 添加 gesture_number 字段
        cursor.execute("""
            ALTER TABLE checkins 
            ADD COLUMN gesture_number INT DEFAULT NULL COMMENT '手势签到指定的数字(1-5)'
        """)
        print("✓ 已添加 gesture_number 字段")
        
        conn.commit()
        print("\n数据库更新成功！")
    except Exception as e:
        if "Duplicate column" in str(e):
            print("字段已存在，跳过")
        else:
            print(f"更新失败: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    update_schema()
