import os
from app import app, db
from app import User
from werkzeug.security import generate_password_hash

# 设置环境变量
os.environ.setdefault('FLASK_ENV', 'production')

# 初始化数据库
def init_db():
    """初始化数据库和默认管理员账户"""
    with app.app_context():
        try:
            db.create_all()
            print("数据库表创建成功")
            
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
            else:
                print("管理员账户已存在")
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            raise

# 初始化数据库
init_db()

# WSGI应用对象
application = app

if __name__ == "__main__":
    from waitress import serve
    print("启动Waitress WSGI服务器...")
    print("服务器地址: http://127.0.0.1:5085")
    serve(app, host='0.0.0.0', port=5085, threads=4)