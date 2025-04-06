@echo off
echo DeFi交易机器人 Docker 启动脚本
echo ============================
echo.

REM 检查Docker是否已安装
docker --version > nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Docker，请先安装Docker
    echo 您可以从 https://docs.docker.com/get-docker/ 获取Docker
    pause
    exit /b 1
)

REM 检查.env文件是否存在
if not exist ".env" (
    echo 创建.env文件...
    copy .env.example .env
    
    REM 提示用户输入OpenRouter API密钥
    set /p api_key=请输入您的OpenRouter API密钥:
    
    REM 更新.env文件
    if defined api_key (
        powershell -Command "(Get-Content .env) -replace 'your_openrouter_api_key_here', '%api_key%' | Set-Content .env"
        echo API密钥已设置
    ) else (
        echo 警告: 未设置API密钥，将使用默认值
    )
)

REM 构建Docker镜像
echo 构建Docker镜像...
docker build -t defi-trade-bot .

REM 允许用户输入自定义交易参数
echo.
set /p customize=您想修改默认的交易参数吗? (y/n):

if /i "%customize%"=="y" (
    set /p max_cost_per_trade=请输入单笔交易的最大成本 (默认: 0.3 USDT):
    set /p max_total_cost=请输入总消耗限额 (默认: 100 USDT):
    set /p wait_between_trades=请输入交易之间的等待时间 (默认: 4秒):
    set /p max_trades=请输入最大交易次数 (默认: 100次):
    
    REM 更新.env文件
    if defined max_cost_per_trade (
        powershell -Command "(Get-Content .env) -replace 'MAX_COST_PER_TRADE=.*', 'MAX_COST_PER_TRADE=%max_cost_per_trade%' | Set-Content .env"
    )
    
    if defined max_total_cost (
        powershell -Command "(Get-Content .env) -replace 'MAX_TOTAL_COST=.*', 'MAX_TOTAL_COST=%max_total_cost%' | Set-Content .env"
    )
    
    if defined wait_between_trades (
        powershell -Command "(Get-Content .env) -replace 'WAIT_BETWEEN_TRADES=.*', 'WAIT_BETWEEN_TRADES=%wait_between_trades%' | Set-Content .env"
    )
    
    if defined max_trades (
        powershell -Command "(Get-Content .env) -replace 'MAX_TRADES=.*', 'MAX_TRADES=%max_trades%' | Set-Content .env"
    )
    
    echo 交易参数已更新
)

REM 运行Docker容器
echo.
echo 启动DeFi交易机器人...
echo 注意: 请在30秒内手动连接钱包
echo.

docker run --rm -it ^
    --name defi-trade-bot ^
    -v "%cd%\.env:/app/.env" ^
    -e DISPLAY=:99 ^
    --network host ^
    defi-trade-bot

echo 交易机器人已停止运行
pause 