"""
Initialize Student Roster Tables
"""
from database import Database

def init_student_roster_tables():
    """初始化学生花名册相关表"""
    print("="*60)
    print("Initializing Student Roster Tables...")
    print("="*60)
    
    try:
        # 读取SQL文件
        with open('student_roster_schema.sql', 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        # 分割SQL语句
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
        
        for statement in statements:
            if statement:
                try:
                    Database.execute_query(statement, commit=True)
                    # 提取表名
                    if 'CREATE TABLE' in statement:
                        table_name = statement.split('CREATE TABLE IF NOT EXISTS')[1].split('(')[0].strip()
                        print(f"✓ Table created: {table_name}")
                except Exception as e:
                    print(f"✗ Error executing statement: {e}")
                    print(f"  Statement: {statement[:100]}...")
        
        print("\n" + "="*60)
        print("Student Roster Tables Initialized Successfully!")
        print("="*60)
        print("\nCreated tables:")
        print("  1. student_roster - 学生花名册")
        print("  2. student_verification_logs - 学生验证记录")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        raise

if __name__ == '__main__':
    init_student_roster_tables()
