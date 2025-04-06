# DeFi 交易机器人

这是一个自动进行USDC和USDT之间交易的机器人，用于获取DeFi平台上的XP奖励。

## 功能特点

- 自动检测哪个代币有余额并进行交易
- 智能切换USDC和USDT之间的交易方向
- 自动点击"ALL"按钮使用最大可用余额
- 使用LLama4 API分析交易页面内容
- 限制每笔交易的最大成本
- 记录交易历史和总消耗

## 使用方法

### 方法1: 使用Docker (最简单)

只需一行命令即可运行机器人！

#### Windows用户:

1. 确保安装了Docker Desktop ([下载链接](https://www.docker.com/products/docker-desktop/))
2. 下载并解压缩此代码包
3. 双击运行 `docker-run.bat`
4. 根据提示输入OpenRouter API密钥和交易参数

#### Mac/Linux用户:

1. 确保安装了Docker ([安装指南](https://docs.docker.com/get-docker/))
2. 下载并解压缩此代码包
3. 打开终端并导航到代码目录
4. 运行以下命令使脚本可执行：
   ```
   chmod +x docker-run.sh
   ```
5. 运行启动脚本：
   ```
   ./docker-run.sh
   ```
6. 根据提示输入OpenRouter API密钥和交易参数

### 方法2: 本地Python环境

#### Windows用户

1. 下载并解压缩代码包
2. 双击运行 `run.bat`
3. 根据提示操作

#### Mac/Linux用户

1. 下载并解压缩代码包
2. 打开终端并导航到代码目录
3. 执行以下命令使脚本可执行：
   ```
   chmod +x run.sh
   ```
4. 运行脚本：
   ```
   ./run.sh
   ```
5. 根据提示操作

## 安装要求

### Docker方式
- Docker

### 本地Python方式
- Python 3.7 或更高版本
- OpenRouter API密钥 (用于LLama4分析)
- 浏览器 (自动通过Playwright安装)

## 配置参数

编辑`.env`文件来自定义以下参数：

- `OPENROUTER_API_KEY`: 您的OpenRouter API密钥
- `MAX_COST_PER_TRADE`: 单笔交易的最大成本 (默认0.3 USDT)
- `MAX_TOTAL_COST`: 总消耗限额 (默认100 USDT)
- `WAIT_BETWEEN_TRADES`: 交易之间的等待时间 (默认4秒)
- `MAX_TRADES`: 最大交易次数 (默认100次)

> **注意**: 使用Docker方式运行时，启动脚本会提示您输入这些参数，无需手动编辑文件。

## 使用说明

1. 脚本会打开浏览器并访问DeFi应用
2. 您需要在30秒内手动连接钱包
3. 连接钱包后，脚本会自动检测余额并开始交易
4. 交易完成后，脚本会自动切换方向并继续下一次交易
5. 脚本会一直运行直到达到最大交易次数或总成本限制

## 高级配置 (Docker)

如果您想进一步自定义Docker容器，可以编辑 `docker-compose.yml` 文件并使用以下命令运行：

```bash
docker-compose up --build
```

这将使用Docker Compose启动容器，并允许更复杂的配置。

## 故障排除

- 如果脚本无法点击按钮，尝试手动点击一次相应按钮，然后重启脚本
- 确保您的浏览器未被其他程序占用
- 如果交易失败，检查您的钱包是否有足够的余额
- Docker版本问题时，尝试运行 `docker system prune -a` 清理缓存后重试

## 免责声明

此脚本仅供学习和参考使用。使用此脚本进行交易风险自负。请确保了解相关平台的规则和风险。 