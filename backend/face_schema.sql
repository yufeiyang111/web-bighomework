-- 用户人脸信息表
CREATE TABLE IF NOT EXISTS user_faces (
    face_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    face_image_path VARCHAR(500),
    face_embedding TEXT NOT NULL COMMENT '人脸特征向量JSON',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户人脸信息表';

-- 人脸登录日志表
CREATE TABLE IF NOT EXISTS face_login_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    login_success BOOLEAN DEFAULT FALSE,
    similarity_score DECIMAL(5,2),
    login_ip VARCHAR(50),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='人脸登录日志表';
