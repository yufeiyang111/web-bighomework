"""
更新签到记录表，添加人脸截图字段
"""
from database import Database

def update_schema():
    """添加人脸截图相关字段到签到记录表"""
    try:
        # 检查字段是否已存在
        check_sql = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'checkin_records' 
            AND COLUMN_NAME = 'face_image_url'
        """
        result = Database.execute_query(check_sql, fetch_one=True)
        
        if not result:
            # 添加人脸截图URL字段（添加到表末尾）
            alter_sql1 = """
                ALTER TABLE checkin_records 
                ADD COLUMN face_image_url VARCHAR(500)
            """
            Database.execute_query(alter_sql1, commit=True)
            print("✓ 添加 face_image_url 字段成功")
        else:
            print("- face_image_url 字段已存在")
        
        # 检查相似度字段
        check_sql2 = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'checkin_records' 
            AND COLUMN_NAME = 'face_similarity'
        """
        result2 = Database.execute_query(check_sql2, fetch_one=True)
        
        if not result2:
            # 添加人脸相似度字段
            alter_sql2 = """
                ALTER TABLE checkin_records 
                ADD COLUMN face_similarity DECIMAL(5, 2)
            """
            Database.execute_query(alter_sql2, commit=True)
            print("✓ 添加 face_similarity 字段成功")
        else:
            print("- face_similarity 字段已存在")
        
        print("\n数据库更新完成！")
        
    except Exception as e:
        print(f"更新失败: {e}")

if __name__ == '__main__':
    update_schema()
