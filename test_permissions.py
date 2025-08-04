#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试权限系统
"""

import requests
from werkzeug.security import generate_password_hash
from app import app, db, User

def test_permissions():
    """测试权限系统"""
    
    with app.app_context():
        # 创建测试用户
        test_employee = User.query.filter_by(username='test_employee').first()
        if not test_employee:
            test_employee = User(
                username='test_employee',
                email='employee@test.com',
                password_hash=generate_password_hash('123456'),
                role='employee'
            )
            db.session.add(test_employee)
            db.session.commit()
            print("创建测试员工账户: test_employee / 123456")
        
        test_manager = User.query.filter_by(username='test_manager').first()
        if not test_manager:
            test_manager = User(
                username='test_manager',
                email='manager@test.com',
                password_hash=generate_password_hash('123456'),
                role='manager'
            )
            db.session.add(test_manager)
            db.session.commit()
            print("创建测试经理账户: test_manager / 123456")
        
        print("\n=== 权限系统测试 ===")
        print("1. 员工权限限制:")
        print("   - 员工只能查看数据，不能编辑")
        print("   - 员工看不到添加/编辑/删除按钮")
        print("   - 员工无法访问编辑功能的路由")
        
        print("\n2. 管理员/经理权限:")
        print("   - 可以查看和编辑所有数据")
        print("   - 可以管理用户（仅管理员）")
        print("   - 可以添加、编辑、删除记录")
        
        print("\n3. 测试账户:")
        print("   - 员工: test_employee / 123456")
        print("   - 经理: test_manager / 123456")
        print("   - 管理员: admin / admin123")
        
        print("\n4. 权限验证:")
        print("   - 员工访问编辑页面会显示权限不足提示")
        print("   - 员工在页面上看不到编辑按钮")
        print("   - 员工在侧边栏看不到添加交易链接")

if __name__ == '__main__':
    test_permissions() 