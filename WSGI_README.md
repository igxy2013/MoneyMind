# WSGI服务器部署说明

本项目已配置为使用Waitress WSGI服务器，适合Windows生产环境部署。

## 快速启动

### 方法1：使用批处理文件（推荐）
```bash
start_wsgi.bat
```

### 方法2：手动启动
```bash
# 安装依赖
pip install -r requirements.txt

# 启动WSGI服务器
python wsgi.py
```

## 服务器配置

- **WSGI服务器**: Waitress 2.1.2
- **监听地址**: 0.0.0.0:5085
- **线程数**: 4
- **访问地址**: http://127.0.0.1:5085

## 文件说明

- `wsgi.py`: WSGI应用入口文件
- `app.py`: Flask应用主文件（仍可用于开发调试）
- `start_wsgi.bat`: Windows启动脚本
- `requirements.txt`: 包含Waitress依赖

## 开发vs生产

### 开发环境
```bash
python app.py
```
使用Flask开发服务器，支持调试模式。

### 生产环境
```bash
python wsgi.py
# 或
start_wsgi.bat
```
使用Waitress WSGI服务器，性能更好，更稳定。

## 优势

1. **性能提升**: Waitress比Flask开发服务器性能更好
2. **稳定性**: 适合生产环境长时间运行
3. **Windows兼容**: 在Windows上表现优异
4. **多线程**: 支持并发请求处理
5. **易于部署**: 无需复杂配置

## 注意事项

- 确保MySQL数据库连接正常
- 检查环境变量配置（.env文件）
- 防火墙需要开放5085端口
- 生产环境建议使用反向代理（如Nginx）