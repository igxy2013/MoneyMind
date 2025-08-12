#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供应商字段迁移脚本
添加 products 字段到 supplier 表
"""

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def migrate_database():
    """执行数据库迁移"""
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        print("开始数据库迁移...")
        
        # 检查 products 字段是否已存在
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'supplier' 
            AND COLUMN_NAME = 'products'
        """, (os.getenv('DB_NAME'),))
        
        if cursor.fetchone():
            print("products 字段已存在，跳过添加")
        else:
            # 添加 products 字段
            cursor.execute("""
                ALTER TABLE supplier 
                ADD COLUMN products TEXT COMMENT '产品信息'
            """)
            print("✓ 已添加 products 字段")
        
        # 更新 supplier_type 字段注释
        cursor.execute("""
            ALTER TABLE supplier 
            MODIFY COLUMN supplier_type VARCHAR(50) 
            COMMENT '供应商类型：生鲜供应商、包装材料供应商、设备供应商、服务供应商'
        """)
        print("✓ 已更新 supplier_type 字段注释")
        
        # 提交更改
        connection.commit()
        print("数据库迁移完成！")
        
    except Exception as e:
        print(f"迁移失败: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    migrate_database()