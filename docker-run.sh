#!/bin/bash

echo "DeFi交易机器人 Docker 启动脚本"
echo "============================"
echo

# 检查Docker是否已安装
if ! command -v docker &> /dev/null; then
    echo "错误: 未检测到Docker，请先安装Docker"
    echo "您可以从 https://docs.docker.com/get-docker/ 获取Docker"
    exit 1
fi

# 检查.env文件是否存在
if [ ! -f ".env" ]; then
    echo "创建.env文件..."
    cp .env.example .env
    
    # 提示用户输入OpenRouter API密钥
    echo "请输入您的OpenRouter API密钥:"
    read -r api_key
    
    # 更新.env文件
    if [ -n "$api_key" ]; then
        sed -i "s/your_openrouter_api_key_here/$api_key/g" .env
        echo "API密钥已设置"
    else
        echo "警告: 未设置API密钥，将使用默认值"
    fi
fi

# 构建Docker镜像
echo "构建Docker镜像..."
docker build -t defi-trade-bot .

# 允许用户输入自定义交易参数
echo
echo "您想修改默认的交易参数吗? (y/n)"
read -r customize

if [ "$customize" = "y" ] || [ "$customize" = "Y" ]; then
    echo "请输入单笔交易的最大成本 (默认: 0.3 USDT):"
    read -r max_cost_per_trade
    
    echo "请输入总消耗限额 (默认: 100 USDT):"
    read -r max_total_cost
    
    echo "请输入交易之间的等待时间 (默认: 4秒):"
    read -r wait_between_trades
    
    echo "请输入最大交易次数 (默认: 100次):"
    read -r max_trades
    
    # 更新.env文件
    if [ -n "$max_cost_per_trade" ]; then
        sed -i "s/MAX_COST_PER_TRADE=.*/MAX_COST_PER_TRADE=$max_cost_per_trade/g" .env
    fi
    
    if [ -n "$max_total_cost" ]; then
        sed -i "s/MAX_TOTAL_COST=.*/MAX_TOTAL_COST=$max_total_cost/g" .env
    fi
    
    if [ -n "$wait_between_trades" ]; then
        sed -i "s/WAIT_BETWEEN_TRADES=.*/WAIT_BETWEEN_TRADES=$wait_between_trades/g" .env
    fi
    
    if [ -n "$max_trades" ]; then
        sed -i "s/MAX_TRADES=.*/MAX_TRADES=$max_trades/g" .env
    fi
    
    echo "交易参数已更新"
fi

# 运行Docker容器
echo
echo "启动DeFi交易机器人..."
echo "注意: 请在30秒内手动连接钱包"
echo

docker run --rm -it \
    --name defi-trade-bot \
    -v "$(pwd)/.env:/app/.env" \
    -e DISPLAY=:99 \
    --network host \
    defi-trade-bot

echo "交易机器人已停止运行" 