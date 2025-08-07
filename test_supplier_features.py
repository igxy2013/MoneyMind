#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试供应商新功能
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Supplier

def test_supplier_model():
    """测试供应商模型的新字段"""
    print("测试供应商模型...")
    
    with app.app_context():
        # 检查表结构
        try:
            suppliers = Supplier.query.limit(1).all()
            print("✓ 供应商模型查询成功")
            
            # 检查新字段是否存在
            if hasattr(Supplier, 'supplier_type'):
                print("✓ supplier_type 字段存在")
            else:
                print("✗ supplier_type 字段不存在")
                
            if hasattr(Supplier, 'supply_categories'):
                print("✓ supply_categories 字段存在")
            else:
                print("✗ supply_categories 字段不存在")
                
            if hasattr(Supplier, 'image_path'):
                print("✓ image_path 字段存在")
            else:
                print("✗ image_path 字段不存在")
                
        except Exception as e:
            print(f"✗ 查询供应商时出错: {e}")

def test_upload_directory():
    """测试上传目录"""
    print("\n测试上传目录...")
    
    upload_dir = 'static/uploads/suppliers'
    if os.path.exists(upload_dir):
        print(f"✓ 上传目录存在: {upload_dir}")
    else:
        print(f"✗ 上传目录不存在: {upload_dir}")
        try:
            os.makedirs(upload_dir, exist_ok=True)
            print(f"✓ 已创建上传目录: {upload_dir}")
        except Exception as e:
            print(f"✗ 创建上传目录失败: {e}")

def test_app_config():
    """测试应用配置"""
    print("\n测试应用配置...")
    
    with app.app_context():
        if app.config.get('UPLOAD_FOLDER'):
            print(f"✓ 上传目录配置: {app.config['UPLOAD_FOLDER']}")
        else:
            print("✗ 上传目录配置缺失")
            
        if app.config.get('MAX_CONTENT_LENGTH'):
            print(f"✓ 最大文件大小配置: {app.config['MAX_CONTENT_LENGTH']} bytes")
        else:
            print("✗ 最大文件大小配置缺失")

def main():
    """主测试函数"""
    print("开始测试供应商新功能...\n")
    
    # 加载环境变量
    load_dotenv()
    
    test_supplier_model()
    test_upload_directory()
    test_app_config()
    
    print("\n测试完成！")
    print("\n下一步操作:")
    print("1. 运行 python migrate_supplier_fields.py 来添加数据库字段")
    print("2. 启动应用并测试新功能")
    print("3. 在供应商管理页面测试添加图片和选择供应商类型")

if __name__ == "__main__":
    main()
