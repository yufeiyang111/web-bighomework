"""插入群聊测试数据"""
from database import Database

def insert_test_data():
    conn = Database.get_connection()
    cursor = conn.cursor()
    
    try:
        # 先查询角色ID
        cursor.execute("SELECT role_id FROM roles WHERE role_name = 'student'")
        student_role = cursor.fetchone()
        student_role_id = student_role['role_id'] if student_role else 3
        
        cursor.execute("SELECT role_id FROM roles WHERE role_name = 'teacher'")
        teacher_role = cursor.fetchone()
        teacher_role_id = teacher_role['role_id'] if teacher_role else 2
        
        # 查询有哪些学生
        cursor.execute("SELECT user_id, real_name FROM users WHERE role_id = %s LIMIT 5", (student_role_id,))
        students = cursor.fetchall()
        print(f"找到 {len(students)} 个学生:")
        for s in students:
            print(f"  - ID: {s['user_id']}, 姓名: {s['real_name']}")
        
        # 查询老师信息
        cursor.execute("SELECT user_id, real_name FROM users WHERE user_id = 3")
        teacher = cursor.fetchone()
        if teacher:
            print(f"\n老师: ID: {teacher['user_id']}, 姓名: {teacher['real_name']}")
        else:
            print("\n未找到ID为3的老师!")
            return
        
        # 查询课程
        cursor.execute("SELECT id, name FROM courses WHERE teacher_id = 3 LIMIT 1")
        course = cursor.fetchone()
        if course:
            print(f"课程: ID: {course['id']}, 名称: {course['name']}")
        
        # 创建测试群组
        print("\n创建测试群组...")
        cursor.execute("""
            INSERT INTO chat_groups (name, description, owner_id, course_id)
            VALUES (%s, %s, %s, %s)
        """, ('测试课程群', '这是一个测试群组，用于测试群聊功能', 3, course['id'] if course else None))
        group_id = cursor.lastrowid
        print(f"✓ 群组创建成功, ID: {group_id}")
        
        # 添加群主（老师）
        cursor.execute("""
            INSERT INTO group_members (group_id, user_id, role)
            VALUES (%s, %s, 'owner')
        """, (group_id, 3))
        print("✓ 群主添加成功")
        
        # 添加学生成员
        for student in students:
            try:
                cursor.execute("""
                    INSERT INTO group_members (group_id, user_id, role)
                    VALUES (%s, %s, 'member')
                """, (group_id, student['user_id']))
                print(f"✓ 成员 {student['real_name']} 添加成功")
            except Exception as e:
                print(f"  添加成员失败: {e}")
        
        # 添加一些测试消息
        print("\n添加测试消息...")
        
        # 系统消息
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender_id, message_type, content)
            VALUES (%s, %s, 'system', %s)
        """, (group_id, 3, '群组"测试课程群"已创建'))
        
        # 老师发的消息
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender_id, message_type, content)
            VALUES (%s, %s, 'text', %s)
        """, (group_id, 3, '欢迎大家加入课程群！有问题可以在群里讨论。'))
        
        # 公告
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender_id, message_type, content)
            VALUES (%s, %s, 'notice', %s)
        """, (group_id, 3, '本周五下午2点有一次随堂测验，请大家做好准备！'))
        
        # 学生发的消息
        if students:
            cursor.execute("""
                INSERT INTO group_messages (group_id, sender_id, message_type, content)
                VALUES (%s, %s, 'text', %s)
            """, (group_id, students[0]['user_id'], '老师好！'))
            
            if len(students) > 1:
                cursor.execute("""
                    INSERT INTO group_messages (group_id, sender_id, message_type, content)
                    VALUES (%s, %s, 'text', %s)
                """, (group_id, students[1]['user_id'], '收到，会好好准备的！'))
        
        # 签到通知
        cursor.execute("""
            INSERT INTO group_messages (group_id, sender_id, message_type, content, reference_type)
            VALUES (%s, %s, 'checkin', %s, 'checkin')
        """, (group_id, 3, '老师发起了签到，请在5分钟内完成签到'))
        
        print("✓ 测试消息添加成功")
        
        conn.commit()
        print("\n" + "=" * 50)
        print("测试数据插入完成！")
        print(f"群组ID: {group_id}")
        print(f"群主: {teacher['real_name']} (ID: 3)")
        print(f"成员数: {len(students) + 1}")
        print("=" * 50)
        
    except Exception as e:
        conn.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    insert_test_data()
