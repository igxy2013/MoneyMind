# 安全配置指南

## 环境变量配置

### 1. 敏感信息保护

项目已配置使用 `.env` 文件来存储敏感信息，避免在代码中硬编码：

```bash
# 数据库配置
DB_HOST=acbim.fun
DB_USER=mysql
DB_PASSWORD=12345678
DB_NAME=MoneyMind

# Flask配置
SECRET_KEY=your-secret-key-here-change-this-in-production
```

### 2. 文件结构

- `.env` - 实际的环境变量文件（不提交到版本控制）
- `env.example` - 环境变量示例文件（可提交到版本控制）
- `setup_env.py` - 环境变量设置脚本

### 3. 安全最佳实践

#### 生产环境配置

1. **修改 SECRET_KEY**：
   ```bash
   # 生成安全的密钥
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **使用强密码**：
   - 数据库密码至少16位
   - 包含大小写字母、数字、特殊字符

3. **环境隔离**：
   - 开发环境：`.env.development`
   - 测试环境：`.env.testing`
   - 生产环境：`.env.production`

#### 安全检查清单

- [ ] 修改默认的 SECRET_KEY
- [ ] 使用强数据库密码
- [ ] 限制数据库访问权限
- [ ] 启用 HTTPS
- [ ] 配置防火墙规则
- [ ] 定期备份数据
- [ ] 监控异常访问

### 4. 部署安全

#### 服务器配置

1. **环境变量设置**：
   ```bash
   # 在服务器上创建 .env 文件
   cp env.example .env
   # 编辑 .env 文件，填入生产环境配置
   ```

2. **文件权限**：
   ```bash
   # 设置 .env 文件权限
   chmod 600 .env
   ```

3. **系统服务**：
   ```bash
   # 使用 systemd 管理服务
   sudo systemctl enable moneymind
   sudo systemctl start moneymind
   ```

### 5. 监控和日志

#### 日志配置

```python
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
if not app.debug:
    file_handler = RotatingFileHandler('logs/moneymind.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('MoneyMind startup')
```

#### 安全监控

1. **访问日志**：记录所有用户访问
2. **错误日志**：记录系统错误和异常
3. **安全日志**：记录登录失败、权限拒绝等
4. **性能监控**：监控系统资源使用

### 6. 数据保护

#### 数据库安全

1. **连接加密**：
   ```python
   # 启用SSL连接
   app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://user:pass@host/db?ssl_ca=/path/to/ca.pem'
   ```

2. **数据备份**：
   ```bash
   # 定期备份数据库
   mysqldump -u mysql -p MoneyMind > backup_$(date +%Y%m%d).sql
   ```

3. **访问控制**：
   ```sql
   -- 限制数据库用户权限
   GRANT SELECT, INSERT, UPDATE, DELETE ON MoneyMind.* TO 'moneymind_user'@'localhost';
   ```

### 7. 应用安全

#### 用户认证

1. **密码策略**：
   - 最小长度：8位
   - 复杂度要求：大小写字母、数字、特殊字符
   - 定期更换：90天

2. **会话管理**：
   ```python
   # 配置会话安全
   app.config['SESSION_COOKIE_SECURE'] = True
   app.config['SESSION_COOKIE_HTTPONLY'] = True
   app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
   ```

3. **权限控制**：
   - 基于角色的访问控制（RBAC）
   - 最小权限原则
   - 定期权限审查

### 8. 网络安全

#### HTTPS配置

1. **SSL证书**：
   ```bash
   # 使用 Let's Encrypt 免费证书
   certbot --nginx -d yourdomain.com
   ```

2. **安全头**：
   ```python
   from flask_talisman import Talisman
   
   Talisman(app, 
       content_security_policy={
           'default-src': "'self'",
           'script-src': "'self' 'unsafe-inline'",
           'style-src': "'self' 'unsafe-inline'"
       }
   )
   ```

### 9. 应急响应

#### 安全事件处理

1. **事件分类**：
   - 低风险：登录失败、权限拒绝
   - 中风险：异常访问、数据泄露
   - 高风险：系统入侵、数据丢失

2. **响应流程**：
   - 立即隔离受影响系统
   - 收集证据和日志
   - 评估影响范围
   - 修复安全漏洞
   - 恢复系统服务
   - 事后分析和改进

### 10. 合规要求

#### 数据保护法规

1. **个人信息保护**：
   - 最小化收集原则
   - 明确使用目的
   - 用户同意机制
   - 数据删除权利

2. **审计要求**：
   - 操作日志记录
   - 数据访问审计
   - 定期安全评估
   - 合规性报告

## 快速设置

### 开发环境

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 设置环境变量
python setup_env.py

# 3. 检查配置
python setup_env.py check

# 4. 启动应用
python app.py
```

### 生产环境

```bash
# 1. 创建生产环境配置
cp env.example .env.production

# 2. 编辑生产环境配置
vim .env.production

# 3. 设置文件权限
chmod 600 .env.production

# 4. 启动服务
sudo systemctl start moneymind
```

## 联系信息

如有安全问题，请联系：
- 邮箱：security@company.com
- 电话：+86-xxx-xxxx-xxxx
- 紧急联系：+86-xxx-xxxx-xxxx 