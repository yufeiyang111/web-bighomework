-- AI聊天机器人相关数据库表

-- 学习资料库表
CREATE TABLE IF NOT EXISTS learning_materials (
    material_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    tags VARCHAR(255),
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id),
    INDEX idx_category (category),
    INDEX idx_tags (tags)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 聊天会话表
CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_name VARCHAR(255) DEFAULT '新对话',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 聊天消息表
CREATE TABLE IF NOT EXISTS chat_messages (
    message_id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    role ENUM('user', 'assistant') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 插入一些示例学习资料
INSERT INTO learning_materials (title, content, category, tags, created_by) VALUES
('Python基础语法', 'Python是一种解释型、面向对象、动态数据类型的高级程序设计语言。基础语法包括：变量定义、数据类型、控制流、函数等。', '编程语言', 'Python,基础', 1),
('Vue3响应式原理', 'Vue3使用Proxy实现响应式系统，相比Vue2的Object.defineProperty有更好的性能和功能。主要API包括ref、reactive、computed等。', '前端框架', 'Vue,前端', 1),
('数据库索引优化', '数据库索引是提升查询性能的关键。B+树索引、哈希索引、全文索引各有特点。合理使用索引可以大幅提升查询效率。', '数据库', 'MySQL,优化', 1),
('RESTful API设计原则', 'RESTful API设计应遵循：使用HTTP方法表示操作、资源用名词表示、使用HTTP状态码、版本控制等原则。', 'API设计', 'REST,后端', 1);
