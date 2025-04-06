#!/usr/bin/env python3
"""
打包DeFi交易机器人为ZIP文件
"""

import os
import zipfile
import datetime

def create_package():
    """创建DeFi交易机器人的分发包"""
    # 获取当前日期作为版本标识
    today = datetime.datetime.now().strftime("%Y%m%d")
    zip_filename = f"defi_trade_bot_{today}.zip"
    
    # 需要包含在ZIP中的文件
    files_to_include = [
        "defi.py",
        "requirements.txt",
        "setup.py",
        ".env.example",
        "run.bat",
        "run.sh",
        "README.md",
        # Docker相关文件
        "Dockerfile",
        "docker-compose.yml",
        "docker-run.sh",
        "docker-run.bat"
    ]
    
    print(f"正在创建分发包: {zip_filename}")
    
    # 创建ZIP文件
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files_to_include:
            if os.path.exists(file):
                zipf.write(file)
                print(f"已添加: {file}")
            else:
                print(f"警告: 文件不存在 {file}")
    
    if os.path.exists(zip_filename):
        print(f"分发包创建成功: {zip_filename}")
        print(f"文件大小: {os.path.getsize(zip_filename) / 1024:.2f} KB")
    else:
        print("创建分发包失败")

if __name__ == "__main__":
    create_package() 