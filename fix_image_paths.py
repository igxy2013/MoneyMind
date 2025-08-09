#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复供应商图片路径脚本
将数据库中的图片路径从 'uploads/suppliers/' 更新为 'static/uploads/suppliers/'
"""

import os
import sys
from dotenv import load_dotenv
import pymysql

# 加载环境变量
load_dotenv()

def fix_image_paths():
    """修复数据库中的图片路径"""
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
            # 查询需要修复的记录
            cursor.execute("""
                SELECT id, image_path 
                FROM supplier_images 
                WHERE image_path LIKE 'uploads/suppliers/%'
            """)
            
            records = cursor.fetchall()
            print(f"找到 {len(records)} 条需要修复的图片路径记录")
            
            if records:
                # 更新路径
                for record_id, old_path in records:
                    new_path = old_path.replace('uploads/suppliers/', 'static/uploads/suppliers/')
                    cursor.execute("""
                        UPDATE supplier_images 
                        SET image_path = %s 
                        WHERE id = %s
                    """, (new_path, record_id))
                    print(f"更新记录 {record_id}: {old_path} -> {new_path}")
                
                # 提交更改
                connection.commit()
                print(f"成功更新了 {len(records)} 条记录")
            else:
                print("没有需要修复的记录")
                
    except Exception as e:
        print(f"修复图片路径时出错: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()
    
    return True

if __name__ == '__main__':
    print("开始修复供应商图片路径...")
    if fix_image_paths():
        print("图片路径修复完成！")
    else:
        print("图片路径修复失败！")
        sys.exit(1)