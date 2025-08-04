@echo off
chcp 65001 >nul
title 七彩果坊企业记账系统 - 安装程序

echo.
echo ========================================
echo    七彩果坊企业记账系统安装程序
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

echo.
echo [信息] 正在安装依赖包...

:: 安装所有依赖
echo [信息] 正在安装Flask...
pip install flask

echo [信息] 正在安装Flask-SQLAlchemy...
pip install flask-sqlalchemy

echo [信息] 正在安装Flask-Login...
pip install flask-login

echo [信息] 正在安装Plotly...
pip install plotly

echo [信息] 正在安装Werkzeug...
pip install werkzeug

echo.
echo [信息] 依赖安装完成！
echo.
echo [信息] 现在可以运行 start.bat 或 quick_start.bat 来启动应用
echo [信息] 或者直接运行: python app.py
echo.
echo [信息] 安装完成！
pause 