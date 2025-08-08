#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
商品表字段迁移脚本
添加 stock, description, image_path 字段到 Product 表
"""

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def migrate_product_fields():
    """为Product表添加新字段"""
    
    # 数据库连接配置
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'moneymind'),
        'charset': 'utf8mb4'
    }
    
    try:
        # 连接数据库
        connection = pymysql.connect(**config)
        cursor = connection.cursor()
        
        print("开始迁移Product表字段...")
        
        # 检查字段是否已存在
        cursor.execute("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'product'
        """, (config['database'],))
        
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"现有字段: {existing_columns}")
        
        # 添加 stock 字段
        if 'stock' not in existing_columns:
            cursor.execute("""
                ALTER TABLE product 
                ADD COLUMN stock INT DEFAULT 0 COMMENT '库存数量'
            """)
            print("✓ 添加 stock 字段成功")
        else:
            print("- stock 字段已存在")
        
        # 添加 description 字段
        if 'description' not in existing_columns:
            cursor.execute("""
                ALTER TABLE product 
                ADD COLUMN description TEXT COMMENT '商品描述'
            """)
            print("✓ 添加 description 字段成功")
        else:
            print("- description 字段已存在")
        
        # 添加 image_path 字段
        if 'image_path' not in existing_columns:
            cursor.execute("""
                ALTER TABLE product 
                ADD COLUMN image_path VARCHAR(255) COMMENT '商品图片路径'
            """)
            print("✓ 添加 image_path 字段成功")
        else:
            print("- image_path 字段已存在")
        
        # 提交更改
        connection.commit()
        print("\n✅ Product表字段迁移完成！")
        
        # 验证字段添加
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'product'
            ORDER BY ORDINAL_POSITION
        """, (config['database'],))
        
        print("\n当前Product表结构:")
        for row in cursor.fetchall():
            column_name, data_type, is_nullable, default_value, comment = row
            print(f"  {column_name}: {data_type} (可空: {is_nullable}, 默认: {default_value}, 注释: {comment})")
        
    except pymysql.Error as e:
        print(f"❌ 数据库错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    
    return True

if __name__ == '__main__':
    print("=" * 50)
    print("MoneyMind - Product表字段迁移")
    print("=" * 50)
    
    success = migrate_product_fields()
    
    if success:
        print("\n🎉 迁移成功完成！")
        print("现在可以重新启动应用程序。")
    else:
        print("\n💥 迁移失败，请检查错误信息。")
    
    print("=" * 50)