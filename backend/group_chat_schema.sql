-- 群聊系统数据库表
USE web_education_system;

-- 群组表
CREATE TABLE IF NOT EXISTS `chat_groups` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL COMMENT '群名称',
  `description` TEXT COMMENT '群描述',
  `avatar_url` VARCHAR(255) DEFAULT NULL COMMENT '群头像',
  `owner_id` INT NOT NULL COMMENT '群主ID',
  `course_id` INT DEFAULT NULL COMMENT '关联课程ID',
  `class_id` INT DEFAULT NULL COMMENT '关联班级ID',
  `max_members` INT DEFAULT 500 COMMENT '最大成员数',
  `is_active` TINYINT(1) DEFAULT 1,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_owner_id` (`owner_id`),
  KEY `idx_course_id` (`course_id`),
  KEY `idx_class_id` (`class_id`),
  CONSTRAINT `fk_group_owner` FOREIGN KEY (`owner_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_group_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_group_class` FOREIGN KEY (`class_id`) REFERENCES `classes` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 群成员表
CREATE TABLE IF NOT EXISTS `group_members` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `group_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `role` ENUM('owner', 'admin', 'member') DEFAULT 'member' COMMENT '成员角色',
  `nickname` VARCHAR(50) DEFAULT NULL COMMENT '群内昵称',
  `is_muted` TINYINT(1) DEFAULT 0 COMMENT '是否被禁言',
  `joined_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_group_user` (`group_id`, `user_id`),
  KEY `idx_group_id` (`group_id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_member_group` FOREIGN KEY (`group_id`) REFERENCES `chat_groups` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_member_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 群消息表
CREATE TABLE IF NOT EXISTS `group_messages` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `group_id` INT NOT NULL,
  `sender_id` INT NOT NULL,
  `message_type` ENUM('text', 'image', 'file', 'video', 'voice', 'system', 'checkin', 'homework', 'exam', 'notice') DEFAULT 'text',
  `content` TEXT COMMENT '消息内容',
  `file_url` VARCHAR(255) DEFAULT NULL,
  `file_name` VARCHAR(255) DEFAULT NULL,
  `file_size` INT DEFAULT NULL,
  `reference_id` INT DEFAULT NULL COMMENT '关联的签到/作业/考试ID',
  `reference_type` VARCHAR(20) DEFAULT NULL COMMENT '关联类型: checkin/homework/exam',
  `is_deleted` TINYINT(1) DEFAULT 0,
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_group_id` (`group_id`),
  KEY `idx_sender_id` (`sender_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_msg_group` FOREIGN KEY (`group_id`) REFERENCES `chat_groups` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_msg_sender` FOREIGN KEY (`sender_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 群消息已读记录表
CREATE TABLE IF NOT EXISTS `group_message_reads` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `message_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `read_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_msg_user` (`message_id`, `user_id`),
  KEY `idx_message_id` (`message_id`),
  KEY `idx_user_id` (`user_id`),
  CONSTRAINT `fk_read_msg` FOREIGN KEY (`message_id`) REFERENCES `group_messages` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_read_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
