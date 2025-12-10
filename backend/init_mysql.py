import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()


def create_database():
    """创建数据库"""
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=os.getenv('MYSQL_PORT', '3306'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '123456789')
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # 创建数据库
            database_name = os.getenv('MYSQL_DATABASE', 'student-grade')
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ 数据库 {database_name} 创建成功")

            # 选择数据库
            cursor.execute(f"USE `{database_name}`")

            # 检查表是否存在，如果不存在则创建（作为备用）
            create_tables_sql = """
            -- 用户表
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(64) UNIQUE NOT NULL,
                email VARCHAR(120) UNIQUE NOT NULL,
                password_hash VARCHAR(256),
                role VARCHAR(20) NOT NULL DEFAULT 'student',
                name VARCHAR(64),
                avatar VARCHAR(200),
                department VARCHAR(100),
                phone VARCHAR(20),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_username (username),
                INDEX idx_email (email),
                INDEX idx_role (role)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 班级表
            CREATE TABLE IF NOT EXISTS classes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                description TEXT,
                teacher_id INT NOT NULL,
                course_id INT,
                max_students INT DEFAULT 100,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id),
                INDEX idx_code (code),
                INDEX idx_teacher_id (teacher_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 学生-班级关联表
            CREATE TABLE IF NOT EXISTS student_classes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                class_id INT NOT NULL,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_student_class (student_id, class_id),
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (class_id) REFERENCES classes(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 课程表
            CREATE TABLE IF NOT EXISTS courses (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                code VARCHAR(20) UNIQUE NOT NULL,
                description TEXT,
                teacher_id INT NOT NULL,
                semester VARCHAR(20) NOT NULL,
                credit FLOAT DEFAULT 3.0,
                hours_per_week INT DEFAULT 3,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id),
                INDEX idx_code (code),
                INDEX idx_teacher_id (teacher_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 成绩表
            CREATE TABLE IF NOT EXISTS scores (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                class_id INT NOT NULL,
                exam_id INT,
                subject VARCHAR(100) NOT NULL,
                score FLOAT NOT NULL,
                total_score FLOAT NOT NULL,
                type ENUM('exam', 'manual', 'imported') DEFAULT 'manual',
                recorded_by INT,
                comments TEXT,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                percentage FLOAT GENERATED ALWAYS AS ((score / total_score) * 100) STORED,
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (recorded_by) REFERENCES users(id),
                INDEX idx_student_id (student_id),
                INDEX idx_class_id (class_id),
                INDEX idx_exam_id (exam_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 考试表
            CREATE TABLE IF NOT EXISTS exams (
                id INT AUTO_INCREMENT PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                class_id INT NOT NULL,
                teacher_id INT NOT NULL,
                question_bank_id INT,
                total_questions INT DEFAULT 0,
                total_score FLOAT DEFAULT 100.0,
                passing_score FLOAT DEFAULT 60.0,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                duration INT,
                status ENUM('draft', 'published', 'ongoing', 'ended') DEFAULT 'draft',
                auto_grade BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (teacher_id) REFERENCES users(id),
                INDEX idx_class_id (class_id),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 题库表
            CREATE TABLE IF NOT EXISTS question_banks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                teacher_id INT NOT NULL,
                is_public BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 选择题表
            CREATE TABLE IF NOT EXISTS mcq_questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question_bank_id INT NOT NULL,
                content TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_option VARCHAR(1) NOT NULL,
                explanation TEXT,
                score FLOAT DEFAULT 1.0,
                difficulty VARCHAR(10) DEFAULT 'medium',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (question_bank_id) REFERENCES question_banks(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 提问表
            CREATE TABLE IF NOT EXISTS questions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                class_id INT NOT NULL,
                teacher_id INT NOT NULL,
                content TEXT NOT NULL,
                type ENUM('individual', 'random') DEFAULT 'individual',
                random_count INT,
                due_date TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES classes(id),
                FOREIGN KEY (teacher_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 提问-学生关联表
            CREATE TABLE IF NOT EXISTS question_students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question_id INT NOT NULL,
                student_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_question_student (question_id, student_id),
                FOREIGN KEY (question_id) REFERENCES questions(id),
                FOREIGN KEY (student_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 回答表
            CREATE TABLE IF NOT EXISTS answers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                question_id INT NOT NULL,
                student_id INT NOT NULL,
                content TEXT NOT NULL,
                likes INT DEFAULT 0,
                is_anonymous BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (question_id) REFERENCES questions(id),
                FOREIGN KEY (student_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 回复表
            CREATE TABLE IF NOT EXISTS replies (
                id INT AUTO_INCREMENT PRIMARY KEY,
                answer_id INT NOT NULL,
                user_id INT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (answer_id) REFERENCES answers(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 聊天室表
            CREATE TABLE IF NOT EXISTS chat_rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                class_id INT UNIQUE NOT NULL,
                name VARCHAR(100),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_id) REFERENCES classes(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 聊天消息表
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                chat_room_id INT NOT NULL,
                user_id INT NOT NULL,
                content TEXT NOT NULL,
                message_type VARCHAR(20) DEFAULT 'text',
                file_url VARCHAR(500),
                is_read BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (chat_room_id) REFERENCES chat_rooms(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                INDEX idx_chat_room_id (chat_room_id),
                INDEX idx_created_at (created_at)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 课程资料表
            CREATE TABLE IF NOT EXISTS course_materials (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_id INT NOT NULL,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                file_type VARCHAR(20),
                file_url VARCHAR(500),
                file_size INT,
                download_count INT DEFAULT 0,
                uploaded_by INT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id),
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 作业表
            CREATE TABLE IF NOT EXISTS assignments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                course_id INT NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT,
                total_score FLOAT DEFAULT 100.0,
                due_date TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (course_id) REFERENCES courses(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 考试结果表
            CREATE TABLE IF NOT EXISTS exam_results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                exam_id INT NOT NULL,
                student_id INT NOT NULL,
                score FLOAT DEFAULT 0.0,
                total_score FLOAT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                submitted_at TIMESTAMP,
                ip_address VARCHAR(45),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_id) REFERENCES exams(id),
                FOREIGN KEY (student_id) REFERENCES users(id),
                UNIQUE KEY unique_exam_student (exam_id, student_id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            -- 学生答案表
            CREATE TABLE IF NOT EXISTS student_answers (
                id INT AUTO_INCREMENT PRIMARY KEY,
                exam_result_id INT NOT NULL,
                question_id INT NOT NULL,
                selected_option VARCHAR(1),
                is_correct BOOLEAN,
                score FLOAT DEFAULT 0.0,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_result_id) REFERENCES exam_results(id),
                FOREIGN KEY (question_id) REFERENCES mcq_questions(id)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """

            # 分割SQL语句并执行
            sql_statements = create_tables_sql.split(';')
            for statement in sql_statements:
                if statement.strip():
                    cursor.execute(statement)

            print("✅ 所有表创建成功")

            # 插入初始数据（示例）
            try:
                # 插入一个管理员/教师用户
                insert_admin_sql = """
                INSERT IGNORE INTO users (username, email, password_hash, role, name, department)
                VALUES ('admin', 'admin@example.com', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'teacher', '系统管理员', '计算机科学系')
                """
                cursor.execute(insert_admin_sql)
                print("✅ 插入示例管理员用户")

            except Error as e:
                print(f"⚠️ 插入初始数据时出错: {e}")

            connection.commit()

    except Error as e:
        print(f"❌ 数据库操作错误: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("✅ MySQL连接已关闭")


def test_connection():
    """测试数据库连接"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST', 'localhost'),
            port=os.getenv('MYSQL_PORT', '3306'),
            user=os.getenv('MYSQL_USER', 'root'),
            password=os.getenv('MYSQL_PASSWORD', '123456789'),
            database=os.getenv('MYSQL_DATABASE', 'student-grade')
        )

        if connection.is_connected():
            print("✅ MySQL数据库连接成功")
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL版本: {version[0]}")

            # 显示所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            print(f"✅ 数据库中有 {len(tables)} 个表:")
            for table in tables:
                print(f"  - {table[0]}")

            cursor.close()
            connection.close()

    except Error as e:
        print(f"❌ 数据库连接失败: {e}")


if __name__ == "__main__":
    print("=== MySQL数据库初始化 ===")
    print("1. 创建数据库和表")
    create_database()
    print("\n2. 测试数据库连接")
    test_connection()
    print("\n✅ 数据库初始化完成")