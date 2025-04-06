#!/bin/bash
echo "DeFi交易机器人启动中..."

# 检查Python是否已安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未检测到Python，请先安装Python 3.7或更高版本"
    echo "您可以从 https://www.python.org/downloads/ 下载Python"
    exit 1
fi

# 检查是否存在虚拟环境，如果不存在则创建
if [ ! -d "venv" ]; then
    echo "正在创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
echo "正在安装依赖..."
source venv/bin/activate
pip install -r requirements.txt

# 安装Playwright浏览器
echo "正在安装Playwright浏览器..."
python -m playwright install chromium

# 检查.env文件是否存在，如果不存在则从示例创建
if [ ! -f ".env" ]; then
    echo "创建.env文件..."
    cp .env.example .env
    echo "请打开.env文件并设置您的OpenRouter API密钥"
    if command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    else
        echo "请手动编辑.env文件设置您的OpenRouter API密钥"
    fi
fi

# 运行脚本
echo "启动交易机器人..."
python defi.py

read -p "按Enter键退出..." 