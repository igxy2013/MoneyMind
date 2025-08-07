#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from app import app, db, Product
from flask_login import login_user
from app import User

def test_api_products():
    """测试API产品路由"""
    with app.app_context():
        print("=== 测试API产品路由 ===")
        
        # 获取测试客户端
        client = app.test_client()
        
        # 获取管理员用户
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("✗ 找不到管理员用户")
            return
        
        # 登录用户
        with client.session_transaction() as sess:
            sess['_user_id'] = str(admin.id)
        
        # 测试API路由
        response = client.get('/api/products')
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.get_data(as_text=True)}")
        
        # 检查产品数据
        products = Product.query.filter_by(is_active=True).all()
        print(f"\n数据库中的活跃产品: {len(products)}个")
        for product in products:
            print(f"  - {product.name}")

if __name__ == '__main__':
    test_api_products()
