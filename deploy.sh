#!/bin/bash

# 七彩果坊企业记账系统部署脚本

echo "开始部署七彩果坊企业记账系统..."

# 1. 安装依赖
echo "安装Python依赖..."
pip install -r requirements_production.txt

# 2. 设置环境变量
export FLASK_ENV=production
export SECRET_KEY="your-production-secret-key-here"

# 3. 初始化数据库
echo "初始化数据库..."
python -c "
from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@company.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print('默认管理员账户已创建 - 用户名: admin, 密码: admin123')
"

# 4. 启动应用
echo "启动应用..."
echo "应用将在 http://your-server-ip:5070 上运行"
echo "默认管理员账户: admin / admin123"

# 使用gunicorn启动（推荐用于生产环境）
gunicorn --bind 0.0.0.0:5070 --workers 4 --timeout 120 wsgi:app

# 或者直接使用Flask启动
# python wsgi.py 