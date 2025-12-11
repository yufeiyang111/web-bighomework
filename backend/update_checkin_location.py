# -*- coding: utf-8 -*-
"""更新签到表，添加位置签到字段"""
from database import Database

def update_schema():
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    try:
        print("=== 更新 checkins 表 ===")
        # 添加 location_lat 字段到 checkins 表
        try:
            cursor.execute("""
                ALTER TABLE checkins 
                ADD COLUMN location_lat DECIMAL(10, 8) DEFAULT NULL COMMENT '签到位置纬度'
            """)
            print("✓ checkins.location_lat 已添加")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("- checkins.location_lat 已存在")
            else:
                print(f"添加失败: {e}")
        
        # 添加 location_lng 字段到 checkins 表
        try:
            cursor.execute("""
                ALTER TABLE checkins 
                ADD COLUMN location_lng DECIMAL(11, 8) DEFAULT NULL COMMENT '签到位置经度'
            """)
            print("✓ checkins.location_lng 已添加")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("- checkins.location_lng 已存在")
            else:
                print(f"添加失败: {e}")
        
        # 添加 location_range 字段到 checkins 表
        try:
            cursor.execute("""
                ALTER TABLE checkins 
                ADD COLUMN location_range INT DEFAULT 50 COMMENT '签到范围（米）'
            """)
            print("✓ checkins.location_range 已添加")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("- checkins.location_range 已存在")
            else:
                print(f"添加失败: {e}")
        
        print("\n=== 更新 checkin_records 表 ===")
        # 添加 location_lat 字段到 checkin_records 表
        try:
            cursor.execute("""
                ALTER TABLE checkin_records 
                ADD COLUMN location_lat DECIMAL(10, 8) DEFAULT NULL COMMENT '学生签到位置纬度'
            """)
            print("✓ checkin_records.location_lat 已添加")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("- checkin_records.location_lat 已存在")
            else:
                print(f"添加失败: {e}")
        
        # 添加 location_lng 字段到 checkin_records 表
        try:
            cursor.execute("""
                ALTER TABLE checkin_records 
                ADD COLUMN location_lng DECIMAL(11, 8) DEFAULT NULL COMMENT '学生签到位置经度'
            """)
            print("✓ checkin_records.location_lng 已添加")
        except Exception as e:
            if "Duplicate column" in str(e):
                print("- checkin_records.location_lng 已存在")
            else:
                print(f"添加失败: {e}")
        
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
