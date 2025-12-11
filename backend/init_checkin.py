# -*- coding: utf-8 -*-
"""初始化签到表"""
import pymysql
from pymysql.cursors import DictCursor

def init_checkin_tables():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='yu6670980506',
        database='web_education_system',
        charset='utf8mb4',
        cursorclass=DictCursor
    )
    cursor = conn.cursor()
    
    try:
        # 创建签到表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkins (
                id INT AUTO_INCREMENT PRIMARY KEY,
                group_id INT,
                creator_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                type ENUM('normal', 'qrcode', 'location', 'question', 'face') DEFAULT 'qrcode',
                checkin_code VARCHAR(20),
                duration INT DEFAULT 5,
                end_time DATETIME,
                description TEXT,
                status ENUM('active', 'ended') DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_group (group_id),
                INDEX idx_creator (creator_id),
                INDEX idx_status (status),
                INDEX idx_code (checkin_code)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✓ checkins 表创建成功")
        
        # 创建签到记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checkin_records (
                id INT AUTO_INCREMENT PRIMARY KEY,
                checkin_id INT NOT NULL,
                user_id INT NOT NULL,
                status ENUM('checked', 'late', 'absent') DEFAULT 'checked',
                checkin_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_checkin_user (checkin_id, user_id),
                INDEX idx_checkin (checkin_id),
                INDEX idx_user (user_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """)
        print("✓ checkin_records 表创建成功")
        
        conn.commit()
        print("\n签到表初始化完成！")
    except Exception as e:
        print(f"错误: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_checkin_tables()
