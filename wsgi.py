import os
from app import app, db
from app import User
from werkzeug.security import generate_password_hash

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'production')

# 创建数据库表
with app.app_context():
    db.create_all()
    
    # 创建默认管理员账户
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@company.com',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("默认管理员账户已创建 - 用户名: admin, 密码: admin123")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5085) 