#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供应商表字段迁移脚本
为供应商表添加新字段：supplier_type, supply_categories, image_path
"""

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def migrate_supplier_fields():
    """为供应商表添加新字段"""
    
    # MySQL连接配置
    mysql_config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', ''),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', ''),
        'charset': 'utf8mb4'
    }
    
    try:
        # 连接MySQL数据库
        print("正在连接MySQL数据库...")
        mysql_conn = pymysql.connect(**mysql_config)
        mysql_cursor = mysql_conn.cursor()
        
        # 检查supplier表是否存在
        mysql_cursor.execute("SHOW TABLES LIKE 'supplier'")
        if not mysql_cursor.fetchone():
            print("错误：supplier表不存在")
            return
        
        # 检查字段是否已存在
        mysql_cursor.execute("DESCRIBE supplier")
        existing_columns = [row[0] for row in mysql_cursor.fetchall()]
        
        print(f"现有字段: {existing_columns}")
        
        # 添加新字段
        new_fields = [
            ('supplier_type', 'VARCHAR(50)'),
            ('supply_categories', 'TEXT'),
            ('image_path', 'VARCHAR(255)')
        ]
        
        for field_name, field_type in new_fields:
            if field_name not in existing_columns:
                try:
                    mysql_cursor.execute(f"ALTER TABLE supplier ADD COLUMN {field_name} {field_type}")
                    print(f"成功添加字段: {field_name}")
                except Exception as e:
                    print(f"添加字段 {field_name} 时出错: {e}")
            else:
                print(f"字段 {field_name} 已存在，跳过")
        
        # 提交更改
        mysql_conn.commit()
        print("迁移完成！")
        
        # 显示更新后的表结构
        mysql_cursor.execute("DESCRIBE supplier")
        print("\n更新后的supplier表结构:")
        for row in mysql_cursor.fetchall():
            print(f"  {row[0]} - {row[1]}")
        
    except Exception as e:
        print(f"迁移过程中出错: {e}")
    finally:
        if 'mysql_conn' in locals():
            mysql_conn.close()

if __name__ == "__main__":
    print("开始供应商表字段迁移...")
    migrate_supplier_fields()
    print("迁移脚本执行完成")
