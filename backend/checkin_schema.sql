-- 签到表
CREATE TABLE IF NOT EXISTS checkins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT,
    creator_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    type ENUM('normal', 'qrcode', 'location', 'question', 'face', 'gesture', 'photo') DEFAULT 'qrcode',
    checkin_code VARCHAR(20),
    duration INT DEFAULT 5,
    end_time DATETIME,
    description TEXT,
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    location_range INT DEFAULT 100,
    question TEXT,
    answer VARCHAR(200),
    gesture_number INT DEFAULT NULL COMMENT '手势签到指定的数字(1-5)',
    status ENUM('active', 'ended') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES chat_groups(id) ON DELETE SET NULL,
    FOREIGN KEY (creator_id) REFERENCES users(user_id),
    INDEX idx_group (group_id),
    INDEX idx_creator (creator_id),
    INDEX idx_status (status),
    INDEX idx_code (checkin_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 签到记录表
CREATE TABLE IF NOT EXISTS checkin_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    checkin_id INT NOT NULL,
    user_id INT NOT NULL,
    status ENUM('checked', 'late', 'absent') DEFAULT 'checked',
    checkin_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    location_lat DECIMAL(10, 8),
    location_lng DECIMAL(11, 8),
    face_image_url VARCHAR(500),
    face_similarity DECIMAL(5, 2),
    FOREIGN KEY (checkin_id) REFERENCES checkins(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE KEY uk_checkin_user (checkin_id, user_id),
    INDEX idx_checkin (checkin_id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 如果表已存在，添加新字段
-- ALTER TABLE checkin_records ADD COLUMN face_image_url VARCHAR(500) AFTER location_lng;
-- ALTER TABLE checkin_records ADD COLUMN face_similarity DECIMAL(5, 2) AFTER face_image_url;
