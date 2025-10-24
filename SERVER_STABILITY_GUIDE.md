# 服务器稳定性问题诊断与解决方案

## 问题描述
项目在服务器运行时，刚开始访问正常，但过一段时间后网页端就访问不了了。

## 常见原因分析

### 1. 数据库连接超时/断开
**症状**: 应用运行一段时间后无响应，数据库相关操作失败
**原因**: MySQL连接池配置不当，连接超时或被服务器主动断开

**解决方案**:
```python
# 在 app.py 中已配置的连接池参数
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,           # 连接池大小
    'pool_timeout': 20,        # 获取连接超时时间
    'pool_recycle': 3600,      # 连接回收时间(1小时)
    'max_overflow': 20,        # 最大溢出连接数
    'pool_pre_ping': True      # 连接前测试连接有效性
}
```

**优化建议**:
- 将 `pool_recycle` 设置为 MySQL `wait_timeout` 的一半
- 启用 `pool_pre_ping` 确保连接有效性
- 监控数据库连接状态

### 2. 内存泄漏
**症状**: 应用内存使用持续增长，最终导致系统资源耗尽
**原因**: 未正确关闭数据库会话、大量数据缓存、循环引用

**解决方案**:
```python
# 确保数据库会话正确关闭
try:
    # 数据库操作
    db.session.commit()
except Exception as e:
    db.session.rollback()
    raise
finally:
    db.session.close()
```

### 3. Waitress服务器配置问题
**症状**: 高并发时响应缓慢或停止响应
**原因**: 线程数配置不当，请求队列积压

**当前配置**:
```python
serve(app, host='0.0.0.0', port=5070, threads=4)
```

**优化建议**:
```python
# 根据服务器配置调整参数
serve(app, 
      host='0.0.0.0', 
      port=5070, 
      threads=8,              # 增加线程数
      connection_limit=1000,   # 连接限制
      cleanup_interval=30,     # 清理间隔
      channel_timeout=120)     # 通道超时
```

### 4. 系统资源限制
**症状**: 系统负载过高，应用无响应
**原因**: CPU、内存、磁盘I/O达到瓶颈

**监控命令**:
```bash
# 查看系统资源使用
top
htop
free -h
df -h

# 查看进程资源使用
ps aux | grep python
```

### 5. 网络连接问题
**症状**: 间歇性连接失败
**原因**: 防火墙规则、网络配置、端口占用

**检查命令**:
```bash
# 检查端口监听状态
netstat -tlnp | grep 5070
ss -tlnp | grep 5070

# 检查防火墙状态
sudo ufw status
sudo firewall-cmd --list-all
```

## 推荐解决方案

### 1. 升级到生产级WSGI服务器
使用 Gunicorn 替代 Waitress (Linux环境):
```bash
# 安装 Gunicorn
pip install gunicorn

# 启动命令
gunicorn --bind 0.0.0.0:5070 --workers 4 --timeout 120 --keep-alive 2 wsgi:app
```

### 2. 添加健康检查端点
```python
@app.route('/health')
def health_check():
    try:
        # 测试数据库连接
        db.session.execute('SELECT 1')
        return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow()}), 200
    except Exception as e:
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
```

### 3. 配置日志记录
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler('logs/moneymind.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### 4. 使用进程管理器
**Systemd 服务配置** (已提供 moneymind.service):
```bash
sudo systemctl enable moneymind
sudo systemctl start moneymind
sudo systemctl status moneymind
```

**Supervisor 配置**:
```ini
[program:moneymind]
command=/path/to/venv/bin/gunicorn --bind 0.0.0.0:5070 --workers 4 wsgi:app
directory=/path/to/moneymind
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/moneymind.log
```

### 5. 数据库优化
```sql
-- 检查 MySQL 配置
SHOW VARIABLES LIKE 'wait_timeout';
SHOW VARIABLES LIKE 'interactive_timeout';

-- 优化建议
SET GLOBAL wait_timeout = 28800;
SET GLOBAL interactive_timeout = 28800;
```

## 监控脚本

创建监控脚本 `monitor.sh`:
```bash
#!/bin/bash
while true; do
    if ! curl -f http://localhost:5070/health > /dev/null 2>&1; then
        echo "$(date): Service is down, restarting..."
        systemctl restart moneymind
    fi
    sleep 60
done
```

## 故障排查步骤

1. **检查应用日志**:
   ```bash
   tail -f /var/log/moneymind.log
   journalctl -u moneymind -f
   ```

2. **检查系统资源**:
   ```bash
   top
   free -h
   df -h
   ```

3. **检查数据库连接**:
   ```bash
   mysql -h localhost -u username -p -e "SHOW PROCESSLIST;"
   ```

4. **检查网络连接**:
   ```bash
   netstat -tlnp | grep 5070
   curl -I http://localhost:5070/health
   ```

5. **重启服务**:
   ```bash
   sudo systemctl restart moneymind
   # 或
   python stop.bat && python start_wsgi.bat
   ```

## 预防措施

1. **定期重启**: 设置定时任务定期重启应用
2. **资源监控**: 使用监控工具(如 Prometheus + Grafana)
3. **负载均衡**: 部署多个实例，使用 Nginx 负载均衡
4. **数据库维护**: 定期优化数据库，清理日志
5. **备份策略**: 定期备份数据库和应用文件

## 联系支持

如果问题持续存在，请提供以下信息：
- 系统环境 (操作系统、Python版本)
- 错误日志
- 系统资源使用情况
- 数据库配置信息