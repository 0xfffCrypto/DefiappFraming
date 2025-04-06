from setuptools import setup, find_packages

setup(
    name="defi-trade-bot",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "playwright>=1.39.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "defi-bot=defi:main",
        ],
    },
    python_requires=">=3.7",
    author="DeFi Bot",
    description="自动进行USDC和USDT之间的交易的机器人",
) 