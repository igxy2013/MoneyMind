@echo off
echo 正在启动MoneyMind WSGI服务器...
echo.

REM 激活虚拟环境（如果存在）
if exist "venv\Scripts\activate.bat" (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
)

REM 安装依赖
echo 检查并安装依赖...
pip install -r requirements.txt

REM 启动WSGI服务器
echo.
echo 启动Waitress WSGI服务器...
echo 服务器将在 http://127.0.0.1:5085 启动
echo 按 Ctrl+C 停止服务器
echo.
python wsgi.py

pause