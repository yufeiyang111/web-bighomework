import os
import subprocess
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def backup_database():
    """备份MySQL数据库"""
    # 获取配置
    host = os.getenv('MYSQL_HOST', 'localhost')
    port = os.getenv('MYSQL_PORT', '3306')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '123456789')
    database = os.getenv('MYSQL_DATABASE', 'student-grade')

    # 创建备份目录
    backup_dir = 'backups'
    os.makedirs(backup_dir, exist_ok=True)

    # 生成备份文件名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f'{database}_backup_{timestamp}.sql')

    # 构建mysqldump命令
    cmd = [
        'mysqldump',
        f'--host={host}',
        f'--port={port}',
        f'--user={user}',
        f'--password={password}',
        '--single-transaction',
        '--routines',
        '--triggers',
        '--events',
        '--hex-blob',
        database
    ]

    try:
        print(f"正在备份数据库 {database}...")

        # 执行备份
        with open(backup_file, 'w', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdout=f,
                stderr=subprocess.PIPE,
                text=True
            )

        if result.returncode == 0:
            # 压缩备份文件
            import gzip
            with open(backup_file, 'rb') as f_in:
                with gzip.open(f'{backup_file}.gz', 'wb') as f_out:
                    f_out.writelines(f_in)

            # 删除原始SQL文件
            os.remove(backup_file)

            file_size = os.path.getsize(f'{backup_file}.gz') / (1024 * 1024)  # MB
            print(f"✅ 数据库备份成功: {backup_file}.gz ({file_size:.2f} MB)")

            # 清理旧备份（保留最近7天）
            cleanup_old_backups(backup_dir, days=7)

        else:
            print(f"❌ 数据库备份失败: {result.stderr}")

    except Exception as e:
        print(f"❌ 备份过程中出错: {e}")


def cleanup_old_backups(backup_dir, days=7):
    """清理旧备份文件"""
    import time
    from pathlib import Path

    cutoff_time = time.time() - (days * 24 * 60 * 60)

    for backup_file in Path(backup_dir).glob('*.sql.gz'):
        if backup_file.stat().st_mtime < cutoff_time:
            try:
                backup_file.unlink()
                print(f"🗑️ 删除旧备份: {backup_file.name}")
            except Exception as e:
                print(f"⚠️ 删除旧备份失败 {backup_file.name}: {e}")


def restore_database(backup_file):
    """恢复MySQL数据库"""
    # 获取配置
    host = os.getenv('MYSQL_HOST', 'localhost')
    port = os.getenv('MYSQL_PORT', '3306')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '123456789')
    database = os.getenv('MYSQL_DATABASE', 'student-grade')

    try:
        print(f"正在恢复数据库 {database}...")

        # 如果是压缩文件，先解压
        if backup_file.endswith('.gz'):
            import gzip
            import tempfile

            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as temp_file:
                with gzip.open(backup_file, 'rb') as f_in:
                    temp_file.write(f_in.read().decode('utf-8'))
                temp_path = temp_file.name

            backup_file = temp_path

        # 构建mysql命令
        cmd = [
            'mysql',
            f'--host={host}',
            f'--port={port}',
            f'--user={user}',
            f'--password={password}',
            database
        ]

        # 执行恢复
        with open(backup_file, 'r', encoding='utf-8') as f:
            result = subprocess.run(
                cmd,
                stdin=f,
                stderr=subprocess.PIPE,
                text=True
            )

        if result.returncode == 0:
            print("✅ 数据库恢复成功")
        else:
            print(f"❌ 数据库恢复失败: {result.stderr}")

    except Exception as e:
        print(f"❌ 恢复过程中出错: {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        if len(sys.argv) > 2:
            restore_database(sys.argv[2])
        else:
            print("请指定要恢复的备份文件")
    else:
        backup_database()