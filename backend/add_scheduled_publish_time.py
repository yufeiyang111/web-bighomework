"""
数据库迁移脚本：添加 scheduled_publish_time 列到 exams 表，并创建 notifications 表
运行方式: python add_scheduled_publish_time.py
"""
import pymysql
import os

def run_migration():
    """执行数据库迁移"""
    # 获取数据库配置
    mysql_host = os.environ.get('MYSQL_HOST', 'localhost')
    mysql_port = int(os.environ.get('MYSQL_PORT', '3306'))
    mysql_user = os.environ.get('MYSQL_USER', 'root')
    mysql_password = os.environ.get('MYSQL_PASSWORD', 'password')
    mysql_database = os.environ.get('MYSQL_DATABASE', 'teacher_system')
    
    connection = None
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=mysql_host,
            port=mysql_port,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 检查 scheduled_publish_time 列是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'exams' 
                AND COLUMN_NAME = 'scheduled_publish_time'
            """, (mysql_database,))
            
            if cursor.fetchone()[0] == 0:
                # 添加 scheduled_publish_time 列
                print("添加 scheduled_publish_time 列到 exams 表...")
                cursor.execute("""
                    ALTER TABLE exams 
                    ADD COLUMN scheduled_publish_time TIMESTAMP NULL 
                    AFTER status
                """)
                print("✓ scheduled_publish_time 列已添加")
            else:
                print("✓ scheduled_publish_time 列已存在")
            
            # 检查 notifications 表是否存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM information_schema.TABLES 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'notifications'
            """, (mysql_database,))
            
            if cursor.fetchone()[0] == 0:
                # 创建 notifications 表
                print("创建 notifications 表...")
                cursor.execute("""
                    CREATE TABLE notifications (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        user_id INT NOT NULL,
                        type ENUM('exam_published', 'exam_reminder', 'score_released', 'system') NOT NULL,
                        title VARCHAR(200) NOT NULL,
                        content TEXT,
                        related_id INT,
                        related_type VARCHAR(50),
                        is_read BOOLEAN DEFAULT FALSE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        read_at TIMESTAMP NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_user_id (user_id),
                        INDEX idx_type (type),
                        INDEX idx_is_read (is_read),
                        INDEX idx_created_at (created_at)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
                print("✓ notifications 表已创建")
            else:
                print("✓ notifications 表已存在")
            
            # 提交更改
            connection.commit()
            print("\n数据库迁移完成！")
            
    except Exception as e:
        print(f"迁移失败: {e}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()

if __name__ == '__main__':
    run_migration()

