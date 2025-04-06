#!/bin/bash

# DeFi交易机器人一键安装启动脚本
# 用法: curl -fsSL https://raw.githubusercontent.com/yourusername/defi-bot/main/one-click-run.sh | bash

echo "====================================="
echo "  DeFi交易机器人 一键安装启动脚本   "
echo "====================================="
echo

# 检查必要工具
for tool in curl unzip docker; do
    if ! command -v $tool &> /dev/null; then
        echo "错误: 请先安装 $tool"
        case $tool in
            curl)
                echo "安装命令: sudo apt-get install -y curl (Ubuntu/Debian)"
                echo "或者: sudo yum install -y curl (CentOS/RHEL)"
                ;;
            unzip)
                echo "安装命令: sudo apt-get install -y unzip (Ubuntu/Debian)"
                echo "或者: sudo yum install -y unzip (CentOS/RHEL)"
                ;;
            docker)
                echo "请访问 https://docs.docker.com/get-docker/ 安装Docker"
                ;;
        esac
        exit 1
    fi
done

# 创建临时目录
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# 下载最新版本
echo "下载DeFi交易机器人..."
curl -L -o defi-bot.zip "https://github.com/yourusername/defi-bot/releases/latest/download/defi_trade_bot_latest.zip"

# 解压文件
echo "解压文件..."
unzip -q defi-bot.zip

# 使脚本可执行
chmod +x docker-run.sh

# 运行Docker脚本
echo "启动Docker容器..."
./docker-run.sh

# 清理临时文件
cd -
rm -rf "$TEMP_DIR" 