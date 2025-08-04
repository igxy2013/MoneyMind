#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本：从SQLite迁移到MySQL
"""

import sqlite3
import pymysql
from datetime import datetime
import sys
import os

def migrate_data():
    """从SQLite迁移数据到MySQL"""
    
    # SQLite数据库文件路径 - 检查多个可能的位置
    sqlite_files = [
        'moneymind.db',
        'instance/moneymind.db'
    ]
    
    sqlite_db = None
    for file_path in sqlite_files:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            sqlite_db = file_path
            break
    
    if not sqlite_db:
        print("错误：没有找到有效的SQLite数据库文件")
        print("如果您没有SQLite数据需要迁移，可以直接使用MySQL数据库")
        print("应用已经成功连接到MySQL并创建了表结构")
        return
    
    print(f"使用SQLite数据库文件: {sqlite_db}")
    
    # MySQL连接配置
    mysql_config = {
        'host': 'acbim.fun',
        'user': 'mysql',
        'password': '12345678',
        'database': 'MoneyMind',
        'charset': 'utf8mb4'
    }
    
    try:
        # 连接SQLite数据库
        print("正在连接SQLite数据库...")
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cursor = sqlite_conn.cursor()
        
        # 检查SQLite数据库中是否有表
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = sqlite_cursor.fetchall()
        
        if not tables:
            print("SQLite数据库中没有表，无需迁移数据")
            return
        
        print(f"发现 {len(tables)} 个表：{[table[0] for table in tables]}")
        
        # 连接MySQL数据库
        print("正在连接MySQL数据库...")
        mysql_conn = pymysql.connect(**mysql_config)
        mysql_cursor = mysql_conn.cursor()
        
        # 迁移用户数据
        print("正在迁移用户数据...")
        try:
            sqlite_cursor.execute("SELECT id, username, email, password_hash, role, is_active, created_at FROM user")
            users = sqlite_cursor.fetchall()
            
            for user in users:
                mysql_cursor.execute("""
                    INSERT INTO user (id, username, email, password_hash, role, is_active, created_at) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    username=VALUES(username), email=VALUES(email), password_hash=VALUES(password_hash), 
                    role=VALUES(role), is_active=VALUES(is_active), created_at=VALUES(created_at)
                """, user)
            print(f"迁移了 {len(users)} 个用户")
        except sqlite3.OperationalError as e:
            print(f"用户表不存在或为空: {e}")
        
        # 迁移分类数据
        print("正在迁移分类数据...")
        try:
            sqlite_cursor.execute("SELECT id, name, type, color, user_id FROM category")
            categories = sqlite_cursor.fetchall()
            
            for category in categories:
                mysql_cursor.execute("""
                    INSERT INTO category (id, name, type, color, user_id) 
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    name=VALUES(name), type=VALUES(type), color=VALUES(color), user_id=VALUES(user_id)
                """, category)
            print(f"迁移了 {len(categories)} 个分类")
        except sqlite3.OperationalError as e:
            print(f"分类表不存在或为空: {e}")
        
        # 迁移供应商数据
        print("正在迁移供应商数据...")
        try:
            sqlite_cursor.execute("SELECT id, name, contact_person, phone, email, address, created_at, is_active FROM supplier")
            suppliers = sqlite_cursor.fetchall()
            
            for supplier in suppliers:
                mysql_cursor.execute("""
                    INSERT INTO supplier (id, name, contact_person, phone, email, address, created_at, is_active) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    name=VALUES(name), contact_person=VALUES(contact_person), phone=VALUES(phone), 
                    email=VALUES(email), address=VALUES(address), created_at=VALUES(created_at), is_active=VALUES(is_active)
                """, supplier)
            print(f"迁移了 {len(suppliers)} 个供应商")
        except sqlite3.OperationalError as e:
            print(f"供应商表不存在或为空: {e}")
        
        # 迁移商品数据
        print("正在迁移商品数据...")
        try:
            sqlite_cursor.execute("SELECT id, name, category, supplier_id, cost_price, selling_price, unit, created_at, is_active FROM product")
            products = sqlite_cursor.fetchall()
            
            for product in products:
                mysql_cursor.execute("""
                    INSERT INTO product (id, name, category, supplier_id, cost_price, selling_price, unit, created_at, is_active) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    name=VALUES(name), category=VALUES(category), supplier_id=VALUES(supplier_id), 
                    cost_price=VALUES(cost_price), selling_price=VALUES(selling_price), unit=VALUES(unit), 
                    created_at=VALUES(created_at), is_active=VALUES(is_active)
                """, product)
            print(f"迁移了 {len(products)} 个商品")
        except sqlite3.OperationalError as e:
            print(f"商品表不存在或为空: {e}")
        
        # 迁移交易数据
        print("正在迁移交易数据...")
        try:
            sqlite_cursor.execute('SELECT id, amount, type, description, date, category_id, user_id, supplier_id, product_id, quantity, unit_price FROM "transaction"')
            transactions = sqlite_cursor.fetchall()
            
            for transaction in transactions:
                mysql_cursor.execute("""
                    INSERT INTO transaction (id, amount, type, description, date, category_id, user_id, supplier_id, product_id, quantity, unit_price) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    amount=VALUES(amount), type=VALUES(type), description=VALUES(description), date=VALUES(date), 
                    category_id=VALUES(category_id), user_id=VALUES(user_id), supplier_id=VALUES(supplier_id), 
                    product_id=VALUES(product_id), quantity=VALUES(quantity), unit_price=VALUES(unit_price)
                """, transaction)
            print(f"迁移了 {len(transactions)} 个交易")
        except sqlite3.OperationalError as e:
            print(f"交易表不存在或为空: {e}")
        
        # 迁移应收款数据
        print("正在迁移应收款数据...")
        try:
            sqlite_cursor.execute("SELECT id, title, amount, status, due_date, created_at, received_at, notes, user_id FROM receivable")
            receivables = sqlite_cursor.fetchall()
            
            for receivable in receivables:
                mysql_cursor.execute("""
                    INSERT INTO receivable (id, title, amount, status, due_date, created_at, received_at, notes, user_id) 
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                    title=VALUES(title), amount=VALUES(amount), status=VALUES(status), due_date=VALUES(due_date), 
                    created_at=VALUES(created_at), received_at=VALUES(received_at), notes=VALUES(notes), user_id=VALUES(user_id)
                """, receivable)
            print(f"迁移了 {len(receivables)} 个应收款")
        except sqlite3.OperationalError as e:
            print(f"应收款表不存在或为空: {e}")
        
        # 提交事务
        mysql_conn.commit()
        
        print("数据迁移完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        if 'mysql_conn' in locals():
            mysql_conn.rollback()
        sys.exit(1)
        
    finally:
        # 关闭连接
        if 'sqlite_conn' in locals():
            sqlite_conn.close()
        if 'mysql_conn' in locals():
            mysql_conn.close()

if __name__ == '__main__':
    print("开始从SQLite迁移数据到MySQL...")
    migrate_data() 