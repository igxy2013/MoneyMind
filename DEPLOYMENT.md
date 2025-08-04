# 七彩果坊企业记账系统部署指南

## 系统要求

- Python 3.8+
- Linux服务器（推荐Ubuntu 20.04+）
- 至少1GB内存
- 至少10GB磁盘空间

## 快速部署

### 1. 克隆项目
```bash
git clone <your-repository-url>
cd MoneyMind
```

### 2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖
```bash
pip install -r requirements_production.txt
```

### 4. 设置环境变量
```bash
export FLASK_ENV=production
export SECRET_KEY="your-production-secret-key-here"
```

### 5. 初始化数据库
```bash
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
```

### 6. 启动应用
```bash
# 使用gunicorn（推荐）
gunicorn --bind 0.0.0.0:5085 --workers 4 --timeout 120 wsgi:app

# 或使用Flask直接启动
python wsgi.py
```

## 使用systemd服务（推荐）

### 1. 复制服务文件
```bash
sudo cp moneymind.service /etc/systemd/system/
```

### 2. 修改服务文件
编辑 `/etc/systemd/system/moneymind.service`，修改以下路径：
- `WorkingDirectory`: 改为你的项目路径
- `Environment`: 改为你的虚拟环境路径
- `SECRET_KEY`: 改为你的生产环境密钥

### 3. 启动服务
```bash
sudo systemctl daemon-reload
sudo systemctl enable moneymind
sudo systemctl start moneymind
sudo systemctl status moneymind
```

### 4. 查看日志
```bash
sudo journalctl -u moneymind -f
```

## 防火墙配置

### Ubuntu/Debian
```bash
sudo ufw allow 5085
```

### CentOS/RHEL
```bash
sudo firewall-cmd --permanent --add-port=5085/tcp
sudo firewall-cmd --reload
```

## 反向代理配置（可选）

### Nginx配置示例
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5085;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/your/moneymind/static;
    }
}
```

## 安全建议

1. **更改默认密码**: 登录后立即更改默认管理员密码
2. **使用HTTPS**: 配置SSL证书
3. **定期备份**: 备份数据库文件
4. **更新依赖**: 定期更新Python包
5. **监控日志**: 定期检查应用日志

## 访问信息

- **URL**: http://your-server-ip:5085
- **默认管理员**: admin / admin123
- **端口**: 5085

## 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   sudo netstat -tlnp | grep 5085
   sudo lsof -i :5085
   ```

2. **权限问题**
   ```bash
   sudo chown -R www-data:www-data /path/to/your/moneymind
   sudo chmod -R 755 /path/to/your/moneymind
   ```

3. **数据库问题**
   ```bash
   # 重新初始化数据库
   rm instance/moneymind.db
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

## 备份和恢复

### 备份数据库
```bash
cp instance/moneymind.db backup/moneymind_$(date +%Y%m%d_%H%M%S).db
```

### 恢复数据库
```bash
cp backup/moneymind_20231201_120000.db instance/moneymind.db
```

## 更新应用

1. 停止服务
   ```bash
   sudo systemctl stop moneymind
   ```

2. 更新代码
   ```bash
   git pull origin main
   ```

3. 更新依赖
   ```bash
   source venv/bin/activate
   pip install -r requirements_production.txt
   ```

4. 重启服务
   ```bash
   sudo systemctl start moneymind
   ``` 