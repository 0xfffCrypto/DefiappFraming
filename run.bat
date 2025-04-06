@echo off
echo DeFi交易机器人启动中...

REM 检查Python是否已安装
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未检测到Python，请先安装Python 3.7或更高版本
    echo 您可以从 https://www.python.org/downloads/ 下载Python
    pause
    exit /b 1
)

REM 检查是否存在虚拟环境，如果不存在则创建
if not exist "venv" (
    echo 正在创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境并安装依赖
echo 正在安装依赖...
call venv\Scripts\activate
pip install -r requirements.txt

REM 安装Playwright浏览器
echo 正在安装Playwright浏览器...
python -m playwright install chromium

REM 检查.env文件是否存在，如果不存在则从示例创建
if not exist ".env" (
    echo 创建.env文件...
    copy .env.example .env
    echo 请打开.env文件并设置您的OpenRouter API密钥
    notepad .env
)

REM 运行脚本
echo 启动交易机器人...
python defi.py

pause 