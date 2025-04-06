FROM python:3.9-slim

# 安装必要的系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    procps \
    && rm -rf /var/lib/apt/lists/*

# 安装Playwright依赖
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcb1 \
    libxkbcommon0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制项目文件
COPY requirements.txt ./
COPY defi.py ./
COPY .env.example ./.env

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 安装Playwright浏览器
RUN python -m playwright install chromium

# 设置环境变量，确保浏览器以无头模式运行
ENV DISPLAY=:99

# 暴露端口(如果需要)
# EXPOSE 8000

# 运行入口命令
ENTRYPOINT ["python", "defi.py"] 