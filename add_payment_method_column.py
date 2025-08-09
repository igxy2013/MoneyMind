#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加payment_method字段到transaction表
"""

import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def add_payment_method_column():
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
        
        # 检查列是否已存在
        cursor.execute("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'transaction' 
            AND COLUMN_NAME = 'payment_method'
        """, (os.getenv('DB_NAME'),))
        
        column_exists = cursor.fetchone()[0]
        
        if column_exists == 0:
            # 添加payment_method列
            cursor.execute("""
                ALTER TABLE transaction 
                ADD COLUMN payment_method VARCHAR(20) DEFAULT '现金'
            """)
            
            # 更新现有记录的payment_method为默认值
            cursor.execute("""
                UPDATE transaction 
                SET payment_method = '现金' 
                WHERE payment_method IS NULL
            """)
            
            connection.commit()
            print("✅ payment_method列添加成功！")
        else:
            print("ℹ️ payment_method列已存在，无需添加。")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"❌ 添加payment_method列失败: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("开始添加payment_method列...")
    success = add_payment_method_column()
    if success:
        print("数据库迁移完成！")
    else:
        print("数据库迁移失败！")