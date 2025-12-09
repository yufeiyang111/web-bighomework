-- 学生花名册表 (Student Roster)
-- 教师上传的学生基本信息和人脸图片
CREATE TABLE IF NOT EXISTS student_roster (
    roster_id INT PRIMARY KEY AUTO_INCREMENT,
    student_name VARCHAR(50) NOT NULL COMMENT '学生姓名',
    student_id_number VARCHAR(20) UNIQUE NOT NULL COMMENT '学号/身份证号',
    gender ENUM('男', '女') COMMENT '性别',
    class_name VARCHAR(50) COMMENT '班级',
    grade VARCHAR(20) COMMENT '年级',
    contact_phone VARCHAR(20) COMMENT '联系电话',
    face_image_path VARCHAR(255) NOT NULL COMMENT '人脸图片存储路径',
    face_encoding TEXT COMMENT '人脸特征编码(JSON格式)',
    uploaded_by INT NOT NULL COMMENT '上传教师ID',
    is_registered BOOLEAN DEFAULT FALSE COMMENT '是否已注册账号',
    registered_user_id INT COMMENT '关联的用户ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id),
    FOREIGN KEY (registered_user_id) REFERENCES users(user_id),
    INDEX idx_student_id (student_id_number),
    INDEX idx_uploaded_by (uploaded_by),
    INDEX idx_is_registered (is_registered)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生花名册';

-- 学生注册验证记录表
CREATE TABLE IF NOT EXISTS student_verification_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    roster_id INT NOT NULL,
    verification_image_path VARCHAR(255) COMMENT '验证时上传的照片路径',
    similarity_score FLOAT COMMENT '人脸相似度分数',
    verification_status ENUM('success', 'failed') NOT NULL,
    verification_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (roster_id) REFERENCES student_roster(roster_id),
    INDEX idx_roster_id (roster_id),
    INDEX idx_verification_time (verification_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='学生验证记录';
