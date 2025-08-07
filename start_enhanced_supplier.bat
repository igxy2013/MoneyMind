@echo off
echo 启动 MoneyMind 供应商管理增强功能...
echo.
echo 检查数据库迁移...
python migrate_supplier_enhanced.py
echo.
echo 测试新功能...
python test_supplier_enhanced.py
echo.
echo 启动应用...
echo 请在浏览器中访问: http://localhost:5000
echo 登录后进入供应商管理页面测试新功能
echo.
echo 新功能包括:
echo - 供应方式选择（产地直供/合作社、本地批发市场供应商等）
echo - 重要程度选择（核心供应商、备用供应商、临时供应商）
echo - 供货品类从商品管理中实时选择
echo - 支持多张供应商场地照片上传
echo - 图片预览和删除功能
echo.
python app.py
pause
