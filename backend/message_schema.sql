-- 私聊会话表
CREATE TABLE IF NOT EXISTS private_conversations (
    conversation_id INT PRIMARY KEY AUTO_INCREMENT,
    user1_id INT NOT NULL,
    user2_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user1_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_conversation (user1_id, user2_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='私聊会话表';

-- 私聊消息表
CREATE TABLE IF NOT EXISTS private_messages (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    conversation_id INT NOT NULL,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    message_type ENUM('text', 'image', 'file', 'video', 'emoji', 'voice', 'video_call', 'voice_call') DEFAULT 'text',
    content TEXT,
    file_url VARCHAR(500),
    file_name VARCHAR(255),
    file_size INT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES private_conversations(conversation_id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_conversation (conversation_id),
    INDEX idx_receiver_read (receiver_id, is_read)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='私聊消息表';

-- 用户在线状态表
CREATE TABLE IF NOT EXISTS user_online_status (
    user_id INT PRIMARY KEY,
    is_online BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    socket_id VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户在线状态表';
