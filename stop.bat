@echo off
chcp 65001 >nul
title 七彩果坊企业记账系统 - 停止服务

echo.
echo ========================================
echo    七彩果坊企业记账系统 - 停止服务
echo ========================================
echo.

echo [信息] 正在查找并停止七彩果坊企业记账系统...

:: 查找并停止Python进程
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo table ^| findstr "python.exe"') do (
    echo [信息] 找到Python进程 PID: %%a
    taskkill /f /pid %%a >nul 2>&1
    if not errorlevel 1 (
        echo [信息] 已停止进程 PID: %%a
    )
)

:: 检查端口5070是否还在使用
netstat -an | findstr ":5070" >nul
if not errorlevel 1 (
    echo [信息] 端口5070仍在使用，正在强制关闭...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5070"') do (
        taskkill /f /pid %%a >nul 2>&1
        echo [信息] 已停止占用端口5070的进程 PID: %%a
    )
) else (
    echo [信息] 端口5070已释放
)

echo.
echo [信息] 服务停止完成！
echo [信息] 如果应用仍在运行，请手动关闭命令行窗口
pause 