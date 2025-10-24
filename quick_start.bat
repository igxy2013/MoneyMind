@echo off
chcp 65001 >nul
title 七彩果坊企业记账系统 - 快速启动

echo.
echo ========================================
echo    七彩果坊企业记账系统
echo ========================================
echo.

echo [信息] 正在启动应用...
echo [信息] 访问地址: http://127.0.0.1:5070
echo [信息] 默认账户: admin / admin123
echo.

python app.py

pause 