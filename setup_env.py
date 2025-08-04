#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境变量设置脚本
"""

import os

def setup_env():
    """设置环境变量文件"""
    
    env_content = """# 数据库配置
DB_HOST=acbim.fun
DB_USER=mysql
DB_PASSWORD=12345678
DB_NAME=MoneyMind

# Flask配置
SECRET_KEY=your-secret-key-here-change-this-in-production

# 应用配置
FLASK_ENV=development
FLASK_DEBUG=True
"""
    
    # 检查.env文件是否已存在
    if os.path.exists('.env'):
        print("⚠️  .env 文件已存在")
        response = input("是否要覆盖现有文件？(y/N): ")
        if response.lower() != 'y':
            print("操作已取消")
            return
    
    # 创建.env文件
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("✅ .env 文件创建成功")
        print("\n=== 环境变量配置 ===")
        print("1. 数据库主机: acbim.fun")
        print("2. 数据库用户: mysql")
        print("3. 数据库名称: MoneyMind")
        print("4. 请修改 SECRET_KEY 为安全的密钥")
        print("\n⚠️  重要提醒:")
        print("- 请将 .env 文件添加到 .gitignore")
        print("- 不要在版本控制中提交敏感信息")
        print("- 生产环境请使用更强的 SECRET_KEY")
        
    except Exception as e:
        print(f"❌ 创建 .env 文件失败: {e}")

def check_env():
    """检查环境变量配置"""
    
    print("=== 环境变量检查 ===")
    
    # 检查.env文件
    if os.path.exists('.env'):
        print("✅ .env 文件存在")
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            for line in lines:
                if line.strip() and not line.startswith('#'):
                    key = line.split('=')[0]
                    print(f"   - {key}")
    else:
        print("❌ .env 文件不存在")
        print("请运行: python setup_env.py")
        return
    
    # 检查环境变量加载
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        db_host = os.getenv('DB_HOST')
        db_user = os.getenv('DB_USER')
        db_name = os.getenv('DB_NAME')
        secret_key = os.getenv('SECRET_KEY')
        
        print("\n=== 当前配置 ===")
        print(f"数据库主机: {db_host}")
        print(f"数据库用户: {db_user}")
        print(f"数据库名称: {db_name}")
        print(f"密钥长度: {len(secret_key) if secret_key else 0}")
        
        if secret_key == 'your-secret-key-here-change-this-in-production':
            print("⚠️  警告: 请修改 SECRET_KEY 为安全的密钥")
        
    except ImportError:
        print("❌ 未安装 python-dotenv")
        print("请运行: pip install python-dotenv")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'check':
        check_env()
    else:
        setup_env() 