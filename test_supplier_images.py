#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试供应商图片功能的脚本
"""

import os
import sys
import sqlite3
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Supplier, SupplierImage

def create_test_supplier_with_images():
    """创建测试供应商和图片数据"""
    with app.app_context():
        # 检查是否已有供应商
        supplier = Supplier.query.first()
        if not supplier:
            # 创建测试供应商
            supplier = Supplier(
                name='测试供应商',
                contact_person='张三',
                phone='13800138000',
                email='test@example.com',
                address='北京市朝阳区测试街道123号',
                supplier_type='原材料供应商',
                supply_categories='电子元件,五金配件',
                is_active=True
            )
            db.session.add(supplier)
            db.session.commit()
            print(f"创建测试供应商: {supplier.name} (ID: {supplier.id})")
        else:
            print(f"使用现有供应商: {supplier.name} (ID: {supplier.id})")
        
        # 检查是否已有图片记录
        existing_images = SupplierImage.query.filter_by(supplier_id=supplier.id).count()
        if existing_images > 0:
            print(f"供应商已有 {existing_images} 张图片")
            return supplier.id
        
        # 创建测试图片记录（使用占位符图片）
        test_images = [
            {
                'filename': 'test_image_1.jpg',
                'description': '供应商厂房外观'
            },
            {
                'filename': 'test_image_2.jpg', 
                'description': '生产车间内部'
            },
            {
                'filename': 'test_image_3.jpg',
                'description': '产品展示区'
            }
        ]
        
        # 确保上传目录存在
        upload_dir = os.path.join('static', 'uploads', 'suppliers')
        os.makedirs(upload_dir, exist_ok=True)
        
        # 创建简单的测试图片文件（SVG格式）
        for i, img_info in enumerate(test_images, 1):
            # 创建SVG测试图片
            svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
  <rect width="100%" height="100%" fill="#f0f0f0"/>
  <text x="50%" y="40%" font-family="Arial, sans-serif" font-size="24" fill="#666" text-anchor="middle">
    测试图片 {i}
  </text>
  <text x="50%" y="60%" font-family="Arial, sans-serif" font-size="16" fill="#999" text-anchor="middle">
    {img_info['description']}
  </text>
  <text x="50%" y="80%" font-family="Arial, sans-serif" font-size="12" fill="#ccc" text-anchor="middle">
    400 x 300 像素
  </text>
</svg>'''
            
            # 保存SVG文件
            filename = f'test_image_{i}.svg'
            filepath = os.path.join(upload_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            
            # 创建数据库记录
            image_record = SupplierImage(
                supplier_id=supplier.id,
                image_path=f'static/uploads/suppliers/{filename}',
                upload_time=datetime.now()
            )
            db.session.add(image_record)
            print(f"创建测试图片: {filename}")
        
        db.session.commit()
        print(f"成功为供应商 {supplier.name} 创建了 {len(test_images)} 张测试图片")
        return supplier.id

if __name__ == '__main__':
    supplier_id = create_test_supplier_with_images()
    print(f"\n测试完成！")
    print(f"请访问: http://localhost:5085/supplier/{supplier_id} 查看供应商详情页面")
    print(f"或访问: http://localhost:5085/suppliers 查看供应商列表")