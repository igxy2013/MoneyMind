#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查SQLite数据库中的表
"""

import sqlite3
import os

def check_sqlite_db():
    """检查SQLite数据库中的表"""
    
    # 检查多个可能的SQLite数据库文件位置
    sqlite_files = [
        'moneymind.db',
        'instance/moneymind.db'
    ]
    
    for sqlite_db in sqlite_files:
        print(f"\n检查文件: {sqlite_db}")
        
        if not os.path.exists(sqlite_db):
            print(f"文件不存在: {sqlite_db}")
            continue
        
        file_size = os.path.getsize(sqlite_db)
        print(f"文件大小: {file_size} 字节")
        
        if file_size == 0:
            print("文件为空")
            continue
        
        try:
            conn = sqlite3.connect(sqlite_db)
            cursor = conn.cursor()
            
            # 检查表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            print(f"发现 {len(tables)} 个表:")
            for table in tables:
                print(f"  - {table[0]}")
                
                # 检查每个表的记录数
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
                    count = cursor.fetchone()[0]
                    print(f"    记录数: {count}")
                    
                    # 显示前几条记录
                    if count > 0:
                        cursor.execute(f"SELECT * FROM {table[0]} LIMIT 3")
                        records = cursor.fetchall()
                        print(f"    前3条记录:")
                        for record in records:
                            print(f"      {record}")
                except Exception as e:
                    print(f"    检查表 {table[0]} 时出错: {e}")
            
            conn.close()
            
        except Exception as e:
            print(f"检查SQLite数据库时出错: {e}")

if __name__ == '__main__':
    check_sqlite_db() 