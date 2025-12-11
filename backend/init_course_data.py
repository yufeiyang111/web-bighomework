# -*- coding: utf-8 -*-
"""初始化课程、班级等测试数据"""
import pymysql
from pymysql.cursors import DictCursor

def init_data():
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
        # 余飞杨老师的 user_id = 3
        teacher_id = 3
        
        # 检查老师是否存在
        cursor.execute("SELECT user_id, real_name FROM users WHERE user_id = %s", (teacher_id,))
        teacher = cursor.fetchone()
        if not teacher:
            print("错误: 找不到 user_id=3 的用户")
            return
        print(f"老师: {teacher['real_name']} (ID: {teacher_id})")
        
        # 1. 插入课程数据
        courses_data = [
            ('Web前端开发', 'WEB001', 'HTML/CSS/JavaScript/Vue.js前端开发技术', teacher_id, '2024-2025-1', 3, 4),
            ('Python程序设计', 'PY001', 'Python基础与应用开发', teacher_id, '2024-2025-1', 3, 3),
            ('数据库原理', 'DB001', 'MySQL数据库设计与应用', teacher_id, '2024-2025-1', 4, 4),
        ]
        
        course_ids = []
        for name, code, desc, tid, semester, credit, hours in courses_data:
            # 检查是否已存在
            cursor.execute("SELECT id FROM courses WHERE code = %s", (code,))
            existing = cursor.fetchone()
            if existing:
                course_ids.append(existing['id'])
                print(f"课程已存在: {name} (ID: {existing['id']})")
            else:
                cursor.execute("""
                    INSERT INTO courses (name, code, description, teacher_id, semester, credit, hours_per_week)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (name, code, desc, tid, semester, credit, hours))
                course_ids.append(cursor.lastrowid)
                print(f"✓ 创建课程: {name} (ID: {cursor.lastrowid})")
        
        # 2. 插入班级数据
        classes_data = [
            ('计算机2201班', 'CS2201', '计算机科学与技术专业2022级1班', teacher_id),
            ('计算机2202班', 'CS2202', '计算机科学与技术专业2022级2班', teacher_id),
            ('软件2201班', 'SE2201', '软件工程专业2022级1班', teacher_id),
        ]
        
        class_ids = []
        for name, code, desc, tid in classes_data:
            cursor.execute("SELECT id FROM classes WHERE code = %s", (code,))
            existing = cursor.fetchone()
            if existing:
                class_ids.append(existing['id'])
                print(f"班级已存在: {name} (ID: {existing['id']})")
            else:
                cursor.execute("""
                    INSERT INTO classes (name, code, description, teacher_id)
                    VALUES (%s, %s, %s, %s)
                """, (name, code, desc, tid))
                class_ids.append(cursor.lastrowid)
                print(f"✓ 创建班级: {name} (ID: {cursor.lastrowid})")
        
        # 3. 关联课程和班级
        for course_id in course_ids:
            for class_id in class_ids:
                try:
                    cursor.execute("""
                        INSERT INTO course_classes (course_id, class_id)
                        VALUES (%s, %s)
                    """, (course_id, class_id))
                except pymysql.err.IntegrityError:
                    pass  # 已存在则跳过
        print("✓ 课程-班级关联完成")
        
        # 先提交课程和班级数据
        conn.commit()
        
        print("\n" + "="*50)
        print("测试数据初始化完成！")
        print(f"课程ID: {course_ids}")
        print(f"班级ID: {class_ids}")
        print(f"老师: {teacher['real_name']} (ID: {teacher_id})")
        print("="*50)
        
    except Exception as e:
        conn.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    init_data()
