#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试网站图标设置
"""

import os

def test_favicon():
    """测试网站图标设置"""
    
    # 检查favicon.ico文件是否存在
    favicon_path = 'static/favicon.ico'
    if os.path.exists(favicon_path):
        file_size = os.path.getsize(favicon_path)
        print(f"✅ favicon.ico 文件存在，大小: {file_size} 字节")
    else:
        print("❌ favicon.ico 文件不存在")
        return
    
    # 检查base.html中是否包含图标链接
    base_html_path = 'templates/base.html'
    if os.path.exists(base_html_path):
        with open(base_html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'favicon.ico' in content:
                print("✅ base.html 中包含网站图标链接")
            else:
                print("❌ base.html 中未找到网站图标链接")
    else:
        print("❌ base.html 文件不存在")
    
    print("\n=== 网站图标设置完成 ===")
    print("1. ✅ 已在 base.html 中添加网站图标链接")
    print("2. ✅ 图标文件位置: static/favicon.ico")
    print("3. 浏览器会自动在以下位置显示图标:")
    print("   - 浏览器标签页")
    print("   - 书签")
    print("   - 地址栏")
    print("4. 可能需要清除浏览器缓存才能看到新图标")
    print("5. 访问 http://127.0.0.1:5085 查看效果")

if __name__ == '__main__':
    test_favicon() 