from flask import Flask
from flask_migrate import Migrate
from models import db
import os

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app)
migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # 初始化迁移仓库
        import subprocess
        import sys

        # 检查是否已初始化迁移
        migration_dir = os.path.join(os.path.dirname(__file__), 'migrations')

        if not os.path.exists(migration_dir):
            print("初始化迁移仓库...")
            subprocess.run([sys.executable, '-m', 'flask', 'db', 'init'])

        print("创建迁移脚本...")
        subprocess.run([sys.executable, '-m', 'flask', 'db', 'migrate', '-m', 'initial migration'])

        print("应用迁移...")
        subprocess.run([sys.executable, '-m', 'flask', 'db', 'upgrade'])

        print("✅ 数据库迁移完成")