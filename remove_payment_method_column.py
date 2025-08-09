#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
删除 payment_method 列的数据库迁移脚本

此脚本用于从 transaction 表中删除 payment_method 列
"""

import os
import sys
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def remove_payment_method_column():
    """
    从 transaction 表中删除 payment_method 列
    """
    try:
        # 连接数据库
        connection = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # 检查列是否存在
            check_column_sql = """
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'transaction' 
            AND COLUMN_NAME = 'payment_method'
            """
            
            cursor.execute(check_column_sql, (os.getenv('DB_NAME'),))
            column_exists = cursor.fetchone()[0]
            
            if column_exists:
                # 删除 payment_method 列
                alter_sql = "ALTER TABLE transaction DROP COLUMN payment_method"
                cursor.execute(alter_sql)
                connection.commit()
                print("✅ payment_method 列已成功删除")
            else:
                print("ℹ️  payment_method 列不存在，无需删除")
                
    except Exception as e:
        print(f"❌ 删除 payment_method 列失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    
    return True

if __name__ == '__main__':
    print("开始删除 payment_method 列...")
    success = remove_payment_method_column()
    
    if success:
        print("\n✅ 数据库迁移完成！")
        print("payment_method 列已从 transaction 表中删除")
    else:
        print("\n❌ 数据库迁移失败！")
        sys.exit(1)