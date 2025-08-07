#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import app, db, Supplier

def update_supplier_data():
    """更新现有供应商的供应方式和重要程度"""
    with app.app_context():
        print("=== 更新供应商数据 ===")
        
        # 获取所有供应商
        suppliers = Supplier.query.all()
        
        for i, supplier in enumerate(suppliers):
            print(f"\n{i+1}. 供应商: {supplier.name}")
            print("请选择供应方式:")
            print("1. 产地直供/合作社")
            print("2. 本地批发市场供应商")
            print("3. 一件代发供应商")
            print("4. 社区本地农户/小农场")
            print("0. 跳过")
            
            choice = input("请输入选择 (0-4): ").strip()
            
            if choice == "1":
                supplier.supply_method = "产地直供/合作社"
            elif choice == "2":
                supplier.supply_method = "本地批发市场供应商"
            elif choice == "3":
                supplier.supply_method = "一件代发供应商"
            elif choice == "4":
                supplier.supply_method = "社区本地农户/小农场"
            elif choice == "0":
                print("跳过供应方式设置")
            else:
                print("无效选择，跳过")
                continue
            
            print("\n请选择重要程度:")
            print("1. 核心供应商")
            print("2. 备用供应商")
            print("3. 临时供应商")
            print("0. 跳过")
            
            choice = input("请输入选择 (0-3): ").strip()
            
            if choice == "1":
                supplier.importance_level = "核心供应商"
            elif choice == "2":
                supplier.importance_level = "备用供应商"
            elif choice == "3":
                supplier.importance_level = "临时供应商"
            elif choice == "0":
                print("跳过重要程度设置")
            else:
                print("无效选择，跳过")
                continue
        
        # 保存更改
        try:
            db.session.commit()
            print("\n✓ 供应商数据更新成功！")
        except Exception as e:
            print(f"\n✗ 更新失败: {e}")
            db.session.rollback()

if __name__ == '__main__':
    update_supplier_data()
