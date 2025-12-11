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

# 检查表是否存在
tables = ['chat_groups', 'group_members', 'group_messages', 'group_message_reads']
for t in tables:
    cursor.execute(f"SHOW TABLES LIKE '{t}'")
    exists = cursor.fetchone()
    print(f"{t}: {'存在' if exists else '不存在'}")

cursor.close()
conn.close()
