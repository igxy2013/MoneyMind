#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
供应商功能增强迁移脚本
1. 创建供应商图片表，支持多张图片
2. 修改供应商表，分离供应方式和重要程度
3. 添加供货品类关联表
"""
import pymysql
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

def migrate_supplier_enhanced():
    # 连接MySQL数据库
    try:
        mysql_conn = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            charset='utf8mb4'
        )
        mysql_cursor = mysql_conn.cursor()
        print("正在连接MySQL数据库...")
    except Exception as e:
        print(f"数据库连接失败: {e}")
        return

    try:
        # 检查supplier_images表是否存在
        mysql_cursor.execute("SHOW TABLES LIKE 'supplier_images'")
        if not mysql_cursor.fetchone():
            # 创建供应商图片表
            mysql_cursor.execute("""
                CREATE TABLE supplier_images (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    supplier_id INT NOT NULL,
                    image_path VARCHAR(255) NOT NULL,
                    upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE CASCADE
                )
            """)
            print("✓ 创建供应商图片表成功")
        else:
            print("✓ 供应商图片表已存在")

        # 检查supplier_supply_categories表是否存在
        mysql_cursor.execute("SHOW TABLES LIKE 'supplier_supply_categories'")
        if not mysql_cursor.fetchone():
            # 创建供应商供货品类关联表
            mysql_cursor.execute("""
                CREATE TABLE supplier_supply_categories (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    supplier_id INT NOT NULL,
                    product_name VARCHAR(100) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES supplier(id) ON DELETE CASCADE
                )
            """)
            print("✓ 创建供应商供货品类关联表成功")
        else:
            print("✓ 供应商供货品类关联表已存在")

        # 检查supplier表是否有新字段
        mysql_cursor.execute("DESCRIBE supplier")
        existing_columns = [row[0] for row in mysql_cursor.fetchall()]
        
        # 添加新字段
        new_fields = [
            ('supply_method', 'VARCHAR(50) COMMENT "供应方式：产地直供/合作社、本地批发市场供应商、一件代发供应商、社区本地农户/小农场"'),
            ('importance_level', 'VARCHAR(50) COMMENT "重要程度：核心供应商、备用供应商、临时供应商"')
        ]
        
        for field_name, field_type in new_fields:
            if field_name not in existing_columns:
                mysql_cursor.execute(f"ALTER TABLE supplier ADD COLUMN {field_name} {field_type}")
                print(f"✓ 成功添加字段: {field_name}")
            else:
                print(f"✓ 字段 {field_name} 已存在")

        # 迁移现有数据
        # 将现有的supplier_type数据迁移到supply_method
        mysql_cursor.execute("SELECT id, supplier_type FROM supplier WHERE supplier_type IS NOT NULL AND supplier_type != ''")
        suppliers = mysql_cursor.fetchall()
        
        for supplier_id, supplier_type in suppliers:
            if supplier_type in ['产地直供/合作社', '本地批发市场供应商', '一件代发供应商', '社区本地农户/小农场']:
                mysql_cursor.execute("UPDATE supplier SET supply_method = %s WHERE id = %s", (supplier_type, supplier_id))
            elif supplier_type in ['核心供应商', '备用供应商', '临时供应商']:
                mysql_cursor.execute("UPDATE supplier SET importance_level = %s WHERE id = %s", (supplier_type, supplier_id))
        
        if suppliers:
            print(f"✓ 迁移了 {len(suppliers)} 个供应商的类型数据")

        # 将现有的supply_categories数据迁移到新表
        mysql_cursor.execute("SELECT id, supply_categories FROM supplier WHERE supply_categories IS NOT NULL AND supply_categories != ''")
        suppliers_with_categories = mysql_cursor.fetchall()
        
        for supplier_id, categories in suppliers_with_categories:
            if categories:
                # 分割品类（假设用逗号分隔）
                category_list = [cat.strip() for cat in categories.split(',') if cat.strip()]
                for category in category_list:
                    mysql_cursor.execute(
                        "INSERT INTO supplier_supply_categories (supplier_id, product_name) VALUES (%s, %s)",
                        (supplier_id, category)
                    )
        
        if suppliers_with_categories:
            print(f"✓ 迁移了 {len(suppliers_with_categories)} 个供应商的品类数据")

        # 将现有的image_path数据迁移到新表
        mysql_cursor.execute("SELECT id, image_path FROM supplier WHERE image_path IS NOT NULL AND image_path != ''")
        suppliers_with_images = mysql_cursor.fetchall()
        
        for supplier_id, image_path in suppliers_with_images:
            mysql_cursor.execute(
                "INSERT INTO supplier_images (supplier_id, image_path) VALUES (%s, %s)",
                (supplier_id, image_path)
            )
        
        if suppliers_with_images:
            print(f"✓ 迁移了 {len(suppliers_with_images)} 个供应商的图片数据")

        mysql_conn.commit()
        print("\n✓ 迁移完成！")
        
        # 显示更新后的表结构
        print("\n更新后的supplier表结构:")
        mysql_cursor.execute("DESCRIBE supplier")
        for row in mysql_cursor.fetchall():
            print(f"  {row[0]} - {row[1]}")
        
        print("\n新创建的表:")
        mysql_cursor.execute("SHOW TABLES LIKE 'supplier_%'")
        for row in mysql_cursor.fetchall():
            print(f"  {row[0]}")

    except Exception as e:
        print(f"迁移过程中出现错误: {e}")
        mysql_conn.rollback()
    finally:
        mysql_cursor.close()
        mysql_conn.close()

if __name__ == "__main__":
    migrate_supplier_enhanced()
