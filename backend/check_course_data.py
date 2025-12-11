# -*- coding: utf-8 -*-
import pymysql
from pymysql.cursors import DictCursor

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='yu6670980506',
    database='web_education_system',
    charset='utf8mb4',
    cursorclass=DictCursor
)
cursor = conn.cursor()

print("=== 课程数据 ===")
cursor.execute("SELECT id, name, code, teacher_id FROM courses")
courses = cursor.fetchall()
for c in courses:
    print(f"  ID:{c['id']}, 名称:{c['name']}, 代码:{c['code']}, 老师ID:{c['teacher_id']}")

print(f"\n总计: {len(courses)} 门课程")

print("\n=== 班级数据 ===")
cursor.execute("SELECT id, name, code, teacher_id FROM classes")
classes = cursor.fetchall()
for c in classes:
    print(f"  ID:{c['id']}, 名称:{c['name']}, 代码:{c['code']}, 老师ID:{c['teacher_id']}")

print(f"\n总计: {len(classes)} 个班级")

print("\n=== 老师信息 ===")
cursor.execute("SELECT user_id, real_name FROM users WHERE user_id = 3")
teacher = cursor.fetchone()
if teacher:
    print(f"  ID:{teacher['user_id']}, 姓名:{teacher['real_name']}")

cursor.close()
conn.close()
