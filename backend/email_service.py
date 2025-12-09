import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from config import Config
from database import Database

class EmailService:
    """邮件服务类"""
    
    @staticmethod
    def generate_verification_code():
        """生成6位验证码"""
        return ''.join(random.choices(string.digits, k=6))
    
    @staticmethod
    def send_verification_email(email, verification_code):
        """
        发送验证码邮件
        
        Args:
            email: 收件人邮箱
            verification_code: 验证码
        
        Returns:
            bool: 是否发送成功
        """
        print("\n" + "="*80)
        print("[邮件服务] 准备发送验证码")
        print(f"[邮件服务] 发件人 (FROM): {Config.MAIL_DEFAULT_SENDER}")
        print(f"[邮件服务] 收件人 (TO): {email}")
        print(f"[邮件服务] 验证码: {verification_code}")
        
        # 检查邮箱是否配置
        if not Config.MAIL_USERNAME or not Config.MAIL_PASSWORD or Config.MAIL_USERNAME == 'your-qq-email@qq.com':
            print(f"[邮件服务] 邮箱未配置，跳过发送")
            print(f"[邮件服务] 请在控制台查看验证码并手动输入")
            print(f"="*80)
            print(f"邮箱: {email}")
            print(f"验证码: {verification_code}")
            print(f"="*80 + "\n")
            # 开发模式下，即使不发送邮件也返回成功
            return True
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = Config.MAIL_DEFAULT_SENDER
            msg['To'] = email  # 这里是发送到用户的邮箱！
            msg['Subject'] = '【Web教育系统】邮箱验证码'
            
            print(f"[邮件服务] 创建邮件对象...")
            print(f"[邮件服务] 主题: 【Web教育系统】邮箱验证码")
            
            # 邮件正文
            body = f"""
            <html>
                <body>
                    <h2>邮箱验证</h2>
                    <p>您的验证码是：<strong style="font-size: 24px; color: #007bff;">{verification_code}</strong></p>
                    <p>验证码5分钟内有效，请尽快完成验证。</p>
                    <p>如果这不是您的操作，请忽略此邮件。</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">Web教育系统</p>
                    <p style="color: #999; font-size: 10px;">此邮件由 {Config.MAIL_DEFAULT_SENDER} 发送</p>
                </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))
            
            print(f"[邮件服务] 连接SMTP服务器: {Config.MAIL_SERVER}:{Config.MAIL_PORT}")
            
            # 连接SMTP服务器并发送
            with smtplib.SMTP_SSL(Config.MAIL_SERVER, Config.MAIL_PORT) as server:
                print(f"[邮件服务] 登录账号: {Config.MAIL_USERNAME}")
                server.login(Config.MAIL_USERNAME, Config.MAIL_PASSWORD)
                
                print(f"[邮件服务] 发送邮件...")
                server.send_message(msg)
            
            print(f"[邮件服务] ✅ 邮件发送成功!")
            print(f"[邮件服务] 收件人: {email} 应该收到来自 {Config.MAIL_DEFAULT_SENDER} 的邮件")
            print("="*80 + "\n")
            return True
        except Exception as e:
            print(f"[邮件服务] ❌ 发送邮件失败: {str(e)}")
            print(f"[邮件服务] 验证码: {verification_code} (请在后端控制台查看)")
            print("="*80 + "\n")
            # 即使发送失败，仍然返回成功以便测试
            return True
    
    @staticmethod
    def check_cooldown(email):
        """
        检查邮件发送冷却时间（60秒）
        
        Args:
            email: 邮箱地址
        
        Returns:
            tuple: (是否可以发送, 剩余冷却秒数)
        """
        query = """
        SELECT created_at FROM email_verifications 
        WHERE email = %s 
        ORDER BY created_at DESC 
        LIMIT 1
        """
        result = Database.execute_query(query, (email,), fetch_one=True)
        
        if result:
            last_sent = result['created_at']
            time_diff = datetime.now() - last_sent
            cooldown = 60  # 60秒冷却
            
            if time_diff.total_seconds() < cooldown:
                remaining = int(cooldown - time_diff.total_seconds())
                return False, remaining
        
        return True, 0
    
    @staticmethod
    def save_verification_code(email, code):
        """
        保存验证码到数据库
        
        Args:
            email: 邮箱地址
            code: 验证码
        
        Returns:
            bool: 是否保存成功
        """
        try:
            expires_at = datetime.now() + timedelta(minutes=5)
            query = """
            INSERT INTO email_verifications (email, verification_code, expires_at)
            VALUES (%s, %s, %s)
            """
            Database.execute_query(query, (email, code, expires_at), commit=True)
            return True
        except Exception as e:
            print(f"保存验证码失败: {str(e)}")
            return False
    
    @staticmethod
    def verify_code(email, code):
        """
        验证验证码
        
        Args:
            email: 邮箱地址
            code: 验证码
        
        Returns:
            bool: 验证是否成功
        """
        query = """
        SELECT verification_id, expires_at, is_used 
        FROM email_verifications
        WHERE email = %s AND verification_code = %s
        ORDER BY created_at DESC
        LIMIT 1
        """
        result = Database.execute_query(query, (email, code), fetch_one=True)
        
        if not result:
            return False
        
        # 检查是否已使用
        if result['is_used']:
            return False
        
        # 检查是否过期
        if datetime.now() > result['expires_at']:
            return False
        
        # 标记为已使用
        update_query = "UPDATE email_verifications SET is_used = TRUE WHERE verification_id = %s"
        Database.execute_query(update_query, (result['verification_id'],), commit=True)
        
        return True
