#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查SQLite中transaction表的情况
"""

import sqlite3

def check_transaction_table():
    """检查transaction表"""
    
    sqlite_db = 'instance/moneymind.db'
    
    try:
        conn = sqlite3.connect(sqlite_db)
        cursor = conn.cursor()
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(transaction)")
        columns = cursor.fetchall()
        print("Transaction表结构:")
        for col in columns:
            print(f"  {col}")
        
        # 尝试不同的查询方式
        print("\n尝试查询transaction表:")
        
        # 方式1：直接查询
        try:
            cursor.execute("SELECT COUNT(*) FROM transaction")
            count = cursor.fetchone()[0]
            print(f"  直接查询 - 记录数: {count}")
        except Exception as e:
            print(f"  直接查询失败: {e}")
        
        # 方式2：使用反引号
        try:
            cursor.execute("SELECT COUNT(*) FROM `transaction`")
            count = cursor.fetchone()[0]
            print(f"  反引号查询 - 记录数: {count}")
        except Exception as e:
            print(f"  反引号查询失败: {e}")
        
        # 方式3：使用方括号
        try:
            cursor.execute("SELECT COUNT(*) FROM [transaction]")
            count = cursor.fetchone()[0]
            print(f"  方括号查询 - 记录数: {count}")
        except Exception as e:
            print(f"  方括号查询失败: {e}")
        
        # 方式4：使用双引号
        try:
            cursor.execute('SELECT COUNT(*) FROM "transaction"')
            count = cursor.fetchone()[0]
            print(f"  双引号查询 - 记录数: {count}")
        except Exception as e:
            print(f"  双引号查询失败: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"检查失败: {e}")

if __name__ == '__main__':
    check_transaction_table() 