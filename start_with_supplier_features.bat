@echo off
echo 启动 MoneyMind 供应商管理新功能测试...
echo.

echo 检查数据库迁移...
python migrate_supplier_fields.py
echo.

echo 测试新功能...
python test_supplier_features.py
echo.

echo 启动应用...
echo 请在浏览器中访问: http://localhost:5000
echo 登录后进入供应商管理页面测试新功能
echo.
echo 新功能包括:
echo - 供应商类型选择
echo - 供货品类填写
echo - 场地照片上传
echo - 供应商详情查看
echo.

python app.py
pause
