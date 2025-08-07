#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试供应商增强功能
"""
import os
import sys
from dotenv import load_dotenv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db, Supplier, SupplierImage, SupplierSupplyCategory, Product

def test_supplier_enhanced():
    print("开始测试供应商增强功能...")
    
    with app.app_context():
        # 测试新模型
        print("\n1. 测试新数据模型...")
        try:
            # 检查Supplier模型的新字段
            supplier = Supplier()
            assert hasattr(supplier, 'supply_method'), "Supplier模型缺少supply_method字段"
            assert hasattr(supplier, 'importance_level'), "Supplier模型缺少importance_level字段"
            print("✓ Supplier模型新字段检查通过")
            
            # 检查SupplierImage模型
            supplier_image = SupplierImage()
            assert hasattr(supplier_image, 'supplier_id'), "SupplierImage模型缺少supplier_id字段"
            assert hasattr(supplier_image, 'image_path'), "SupplierImage模型缺少image_path字段"
            print("✓ SupplierImage模型检查通过")
            
            # 检查SupplierSupplyCategory模型
            supply_category = SupplierSupplyCategory()
            assert hasattr(supply_category, 'supplier_id'), "SupplierSupplyCategory模型缺少supplier_id字段"
            assert hasattr(supply_category, 'product_name'), "SupplierSupplyCategory模型缺少product_name字段"
            print("✓ SupplierSupplyCategory模型检查通过")
            
        except Exception as e:
            print(f"✗ 数据模型测试失败: {e}")
            return False
    
    # 测试API路由
    print("\n2. 测试API路由...")
    try:
        with app.test_client() as client:
            # 测试获取商品列表API
            response = client.get('/api/products')
            assert response.status_code == 302, "API需要登录"
            print("✓ API路由检查通过")
    except Exception as e:
        print(f"✗ API路由测试失败: {e}")
    
    # 测试上传目录
    print("\n3. 测试上传目录...")
    upload_dir = 'static/uploads/suppliers'
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir, exist_ok=True)
        print(f"✓ 创建上传目录: {upload_dir}")
    else:
        print(f"✓ 上传目录已存在: {upload_dir}")
    
    print("\n✓ 供应商增强功能测试完成！")
    print("\n下一步操作:")
    print("1. 启动应用: python app.py")
    print("2. 访问供应商管理页面测试新功能")
    print("3. 测试多张图片上传功能")
    print("4. 测试供货品类从商品管理中选择")
    print("5. 测试供应方式和重要程度的分离")
    
    return True

if __name__ == "__main__":
    test_supplier_enhanced()
