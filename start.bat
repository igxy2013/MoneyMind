@echo off
chcp 65001 >nul
title 七彩果坊企业记账系统

echo.
echo ========================================
echo    七彩果坊企业记账系统启动器
echo ========================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] 检测到Python环境
python --version

:: 检查依赖文件是否存在
if not exist "requirements.txt" (
    echo [错误] 未找到requirements.txt文件
    pause
    exit /b 1
)

:: 检查主程序文件是否存在
if not exist "app.py" (
    echo [错误] 未找到app.py文件
    pause
    exit /b 1
)

echo.
echo [信息] 正在检查依赖包...

:: 检查并安装依赖
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装Flask...
    pip install flask
)

python -c "import flask_sqlalchemy" >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装Flask-SQLAlchemy...
    pip install flask-sqlalchemy
)

python -c "import flask_login" >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装Flask-Login...
    pip install flask-login
)

python -c "import plotly" >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装Plotly...
    pip install plotly
)

echo [信息] 依赖检查完成

:: 检查端口是否被占用
netstat -an | findstr ":5085" >nul
if not errorlevel 1 (
    echo [警告] 端口5085已被占用，正在尝试关闭...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5085"') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)

echo.
echo [信息] 正在启动七彩果坊企业记账系统...
echo [信息] 应用将在以下地址运行:
echo    本地访问: http://127.0.0.1:5085
echo    网络访问: http://本机IP:5085
echo.
echo [信息] 默认管理员账户:
echo    用户名: admin
echo    密码: admin123
echo.
echo [提示] 按 Ctrl+C 停止服务
echo ========================================
echo.
git pull
:: 启动应用
python app.py

echo.
echo [信息] 应用已停止
pause 