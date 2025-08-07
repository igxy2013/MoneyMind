#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import app, db, Supplier, SupplierSupplyCategory

def test_supplier_data():
    """测试供应商数据是否正确保存"""
    with app.app_context():
        print("=== 供应商数据测试 ===")
        
        # 获取所有供应商
        suppliers = Supplier.query.all()
        print(f"找到 {len(suppliers)} 个供应商:")
        
        for supplier in suppliers:
            print(f"\n供应商: {supplier.name}")
            print(f"  - 供应方式: {supplier.supply_method or '未设置'}")
            print(f"  - 重要程度: {supplier.importance_level or '未设置'}")
            print(f"  - 供货品类:")
            
            # 获取供货品类
            categories = SupplierSupplyCategory.query.filter_by(supplier_id=supplier.id).all()
            if categories:
                for cat in categories:
                    print(f"    * {cat.product_name}")
            else:
                print("    * 无")
            
            # 获取图片
            images = supplier.images
            print(f"  - 图片数量: {len(images)}")
            for img in images:
                print(f"    * {img.image_path}")

if __name__ == '__main__':
    test_supplier_data()
