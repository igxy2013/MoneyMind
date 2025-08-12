#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
添加供应商备注字段的数据库迁移脚本
"""

import pymysql
import os

# MySQL 数据库配置
DATABASE_CONFIG = {
    'host': '192.168.0.60',
    'user': 'mysql',
    'password': '12345678',
    'database': 'MoneyMind',
    'charset': 'utf8mb4'
}

def add_supplier_notes_column():
    """添加 notes 列到 supplier 表"""
    try:
        # 连接 MySQL 数据库
        connection = pymysql.connect(**DATABASE_CONFIG)
        
        with connection.cursor() as cursor:
            # 检查列是否已存在
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'supplier' 
                AND COLUMN_NAME = 'notes'
            """, (DATABASE_CONFIG['database'],))
            
            exists = cursor.fetchone()[0]
            
            if exists == 0:
                # 添加 notes 列
                cursor.execute("""
                    ALTER TABLE supplier 
                    ADD COLUMN notes TEXT COMMENT '备注信息'
                """)
                connection.commit()
                print("✅ 成功添加 notes 列到 supplier 表")
            else:
                print("ℹ️  notes 列已存在，跳过添加")
                
    except Exception as e:
        print(f"❌ 添加 notes 列失败: {e}")
        if 'connection' in locals():
            connection.rollback()
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == '__main__':
    add_supplier_notes_column()