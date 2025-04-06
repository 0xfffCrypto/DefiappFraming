import asyncio
import time
import re
import os
import json
import requests
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv
import base64

# 加载环境变量
load_dotenv()

# OpenRouter API配置
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
LLAMA4_MODEL = "meta-llama/llama-4-maverick:free"  # 可以根据OpenRouter支持的模型替换

# 交易参数设置
MAX_COST_PER_TRADE = float(os.getenv("MAX_COST_PER_TRADE", "0.3"))  # 最大接受的交易成本（USDT）
MAX_TOTAL_COST = float(os.getenv("MAX_TOTAL_COST", "100"))      # 最大总交易成本（USDT）
WAIT_BETWEEN_TRADES = int(os.getenv("WAIT_BETWEEN_TRADES", "4"))   # 交易间隔（秒）
MAX_TRADES = int(os.getenv("MAX_TRADES", "100"))  # 最大交易次数

# 交易日志
transactions = []
total_cost = 0

# 使用LLama4通过OpenRouter进行分析
async def analyze_with_llm(screenshot_path, current_status):
    try:
        # 读取截图并编码为base64
        with open(screenshot_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # 准备OpenRouter API请求
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost",  # OpenRouter要求的referer
            "X-Title": "DeFi Trading Assistant"  # 应用名称
        }
        
        payload = {
            "model": LLAMA4_MODEL,
            "messages": [
                {"role": "system", "content": "你是一个DeFi交易助手，帮助分析交易页面并提供决策建议。"},
                {"role": "user", "content": [
                    {"type": "text", "text": f"""
                    分析这个DeFi交易页面截图，提取以下信息:
                    1. 当前USDC和USDT余额
                    2. 预计交易成本
                    3. 预计获得的XP
                    4. 是否建议执行交易（如果成本超过{MAX_COST_PER_TRADE} USDT，则不建议）
                    
                    当前状态: {current_status}
                    """},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded_image}"}}
                ]}
            ]
        }
        
        # 发送请求到OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            print(f"API请求错误: {response.status_code} - {response.text}")
            return "API请求失败，无法分析截图。"
    except Exception as e:
        print(f"LLM分析错误: {e}")
        return "无法分析，请手动检查。"

async def extract_cost_from_page(page):
    try:
        # 尝试找到Cost区域
        cost_text = await page.locator("text=Cost").first.text_content()
        cost_element = await page.locator("text=Cost").first.evaluate("el => el.nextElementSibling ? el.nextElementSibling.textContent : null")
        if cost_element:
            cost_match = re.search(r"\$?(\d+\.\d+)", cost_element)
            if cost_match:
                return float(cost_match.group(1))
    except Exception as e:
        print(f"从Cost标签提取成本失败: {e}")
    
    try:
        # 备选方案：查找屏幕上可能的成本数字
        cost_elements = await page.locator("text=/Cost.+\\$\\d+\\.\\d+/").all()
        for element in cost_elements:
            content = await element.text_content()
            cost_match = re.search(r"\$(\d+\.\d+)", content)
            if cost_match:
                return float(cost_match.group(1))
    except Exception as e:
        print(f"从屏幕提取成本失败: {e}")
    
    # 默认值
    print("无法找到成本，返回默认值0.2")
    return 0.2

async def get_viewport_dimensions(page):
    """获取当前页面视图尺寸"""
    return await page.evaluate('() => { return {width: window.innerWidth, height: window.innerHeight} }')

async def click_swap_button(page):
    """
    尝试使用多种方法点击Swap按钮
    优先使用DeFi应用提供的特定选择器
    """
    try:
        # 直接使用提供的Swap按钮选择器
        swap_button = await page.locator('button[data-testid="swap-swap-button"]').first
        if swap_button:
            await swap_button.click()
            print("成功点击Swap按钮 (通过data-testid)")
            return True
    except Exception as e:
        print(f"使用data-testid查找Swap按钮失败: {e}")
    
    try:
        # 使用ID选择器
        swap_button = await page.locator('#swap-swap-button').first
        if swap_button:
            await swap_button.click()
            print("成功点击Swap按钮 (通过ID)")
            return True
    except Exception as e:
        print(f"使用ID查找Swap按钮失败: {e}")
    
    try:
        # 使用文本内容
        swap_button = await page.locator('button:has-text("Swap")').first
        if swap_button:
            await swap_button.click()
            print("成功点击Swap按钮 (通过文本)")
            return True
    except Exception as e:
        print(f"使用文本查找Swap按钮失败: {e}")
    
    try:
        # 使用类选择器和文本的组合
        await page.click('button.bg-action-primary:has-text("Swap")')
        print("成功点击Swap按钮 (通过类+文本)")
        return True
    except Exception as e:
        print(f"使用类+文本查找Swap按钮失败: {e}")
    
    try:
        # 最后尝试：直接使用JavaScript执行点击
        await page.evaluate('''
            (() => {
                // 尝试各种选择器
                const selectors = [
                    'button[data-testid="swap-swap-button"]',
                    '#swap-swap-button',
                    'button.bg-action-primary',
                    'button:has-text("Swap")'
                ];
                
                for (const selector of selectors) {
                    const button = document.querySelector(selector);
                    if (button) {
                        button.click();
                        return true;
                    }
                }
                
                // 查找底部的大按钮
                const buttons = Array.from(document.querySelectorAll('button'));
                const viewport_height = window.innerHeight;
                for (const button of buttons) {
                    const rect = button.getBoundingClientRect();
                    if (rect.y > viewport_height * 0.7 && rect.width > 100) {
                        button.click();
                        return true;
                    }
                }
                
                return false;
            })()
        ''')
        print("尝试通过JavaScript点击Swap按钮")
        return True
    except Exception as e:
        print(f"JavaScript点击Swap按钮失败: {e}")
    
    return False

async def click_reverse_button(page):
    """
    尝试使用多种方法点击代币切换/反转按钮
    通常这个按钮位于两个代币选择框之间
    """
    print("尝试点击交易方向反转按钮...")
    
    # 多次尝试，确保点击成功
    for attempt in range(3):
        try:
            # 使用提供的精确元素选择器
            await page.click('button.size-10\\.5.-translate-x-1\\/2.-translate-y-1\\/2:has(.lucide-arrow-up-down)')
            print("成功点击反转按钮 (通过提供的精确选择器)")
            return True
        except Exception:
            print(f"尝试 {attempt+1}: 使用精确选择器失败")
        
        try:
            # 尝试使用lucide-arrow-up-down类选择器
            await page.click('button:has(.lucide-arrow-up-down)')
            print("成功点击反转按钮 (通过lucide-arrow-up-down图标)")
            return True
        except Exception:
            print(f"尝试 {attempt+1}: 使用lucide-arrow-up-down选择器失败")
        
        try:
            # 尝试点击带有数据属性的反转按钮
            await page.click('button[data-testid="swap-switch-tokens-button"]')
            print("成功点击反转按钮 (通过data-testid)")
            return True
        except Exception:
            print(f"尝试 {attempt+1}: 使用data-testid选择器失败")
        
        try:
            # 尝试使用绝对位置定位
            await page.click('button.absolute.left-1\\/2.top-1\\.5')
            print("成功点击反转按钮 (通过位置选择器)")
            return True
        except Exception:
            print(f"尝试 {attempt+1}: 使用位置选择器失败")
        
        try:
            # 尝试通过类属性和SVG子元素查找
            await page.click('button:has(svg.lucide-arrow-up-down)')
            print("成功点击反转按钮 (通过SVG选择器)")
            return True
        except Exception:
            print(f"尝试 {attempt+1}: 使用SVG选择器失败")
        
        try:
            # 尝试通过各种常见的反转图标文本查找
            for symbol in ['↑↓', '⇅', '⇵', '↕', '↓↑', '⇆']:
                try:
                    reverse_button = await page.locator(f'button:has-text("{symbol}")').first
                    if reverse_button:
                        await reverse_button.click()
                        print(f"成功点击反转按钮 (通过符号 {symbol})")
                        return True
                except Exception:
                    continue
            print(f"尝试 {attempt+1}: 使用符号文本失败")
        except Exception:
            pass
        
        try:
            # 精确定位屏幕中央附近的按钮
            # 先获取视口大小
            viewport = await page.evaluate('''() => {
                return {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            }''')
            
            center_x = viewport['width'] / 2
            top_center_y = viewport['height'] * 0.3  # 大约在屏幕上部 1/3 处
            
            # 使用evaluate查找最接近位置的按钮
            found = await page.evaluate('''({centerX, topCenterY}) => {
                const buttons = Array.from(document.querySelectorAll('button'));
                
                // 找到最接近中心的按钮
                let closestButton = null;
                let minDistance = Infinity;
                
                for (const button of buttons) {
                    const rect = button.getBoundingClientRect();
                    const buttonCenterX = rect.left + rect.width / 2;
                    const buttonCenterY = rect.top + rect.height / 2;
                    
                    // 计算到目标位置的距离
                    const distance = Math.sqrt(
                        Math.pow(buttonCenterX - centerX, 2) + 
                        Math.pow(buttonCenterY - topCenterY, 2)
                    );
                    
                    // 只考虑小按钮（可能是反转按钮）
                    if (rect.width < 60 && rect.height < 60 && distance < minDistance) {
                        minDistance = distance;
                        closestButton = button;
                    }
                }
                
                // 如果找到了按钮，点击它
                if (closestButton && minDistance < 100) {
                    closestButton.click();
                    return true;
                }
                
                return false;
            }''', {'centerX': center_x, 'topCenterY': top_center_y})
            
            if found:
                print("成功点击反转按钮 (通过计算屏幕中央最近的按钮)")
                return True
            else:
                print(f"尝试 {attempt+1}: 通过计算中央位置点击失败")
        except Exception as e:
            print(f"尝试 {attempt+1}: 计算中央位置时出错: {e}")
        
        # 如果所有方法失败，短暂等待后重试
        await asyncio.sleep(1)
    
    # 最后的尝试：直接使用页面坐标点击反转按钮的位置
    try:
        # 假设按钮在页面中央偏上的位置
        viewport = await page.evaluate('() => { return {width: window.innerWidth, height: window.innerHeight} }')
        center_x = viewport['width'] / 2
        center_y = viewport['height'] * 0.3
        
        # 点击该位置
        await page.mouse.click(center_x, center_y)
        print("尝试使用绝对坐标点击反转按钮位置")
        return True
    except Exception as e:
        print(f"使用绝对坐标点击失败: {e}")
    
    print("所有点击反转按钮的尝试均失败")
    return False

async def ensure_swap_direction(page, current_from_token, current_to_token):
    """确保交易方向正确，如果不正确则调整"""
    for attempt in range(3):  # 最多尝试3次
        try:
            # 获取当前显示的代币顺序
            token_elements = await page.locator("text=/USDC|USDT/").all()
            if len(token_elements) >= 2:
                from_token_text = await token_elements[0].text_content()
                to_token_text = await token_elements[1].text_content()
                
                detected_from = "USDC" if "USDC" in from_token_text else "USDT"
                detected_to = "USDT" if "USDT" in to_token_text else "USDC"
                
                print(f"检测到当前交易方向: {detected_from} -> {detected_to}")
                
                # 如果方向不匹配预期，点击反转按钮
                if detected_from != current_from_token or detected_to != current_to_token:
                    print(f"交易方向不匹配，需要反转 (当前: {detected_from}->{detected_to}, 预期: {current_from_token}->{current_to_token})")
                    if await click_reverse_button(page):
                        print("已点击反转按钮调整交易方向")
                        await asyncio.sleep(1)  # 等待UI更新
                        
                        # 再次检查方向是否正确
                        continue
                    else:
                        print(f"尝试 {attempt+1}: 无法调整交易方向")
                else:
                    print("交易方向已正确")
                    return True
            else:
                print(f"尝试 {attempt+1}: 无法检测到代币文本")
        except Exception as e:
            print(f"尝试 {attempt+1}: 检查交易方向时出错: {e}")
        
        await asyncio.sleep(1)
    
    print("无法确保交易方向正确")
    return False

async def confirm_transaction(page):
    try:
        # 等待并点击确认按钮
        confirm_button = await page.wait_for_selector("button:has-text('Confirm')", timeout=2500)
        if confirm_button:
            await confirm_button.click()
            print("已点击确认按钮")
    except Exception:
        print("未找到确认按钮，可能不需要确认")
    
    try:
        # 等待交易完成的通知
        success = await page.wait_for_selector("text=/Transaction (Submitted|Confirmed)/", timeout=5000)
        if success:
            print("交易已提交/确认")
            return True
    except Exception:
        print("未捕获到交易成功通知")
    
    # 无论如何等待一段时间让交易完成
    await asyncio.sleep(5.5)
    return True

async def extract_balances_from_page(page):
    """
    从页面提取USDC和USDT余额信息
    返回包含余额的字典
    """
    balances = {"USDC": 0.0, "USDT": 0.0}
    
    try:
        # 尝试从页面提取余额信息
        balance_elements = await page.locator("text=/Balance: [0-9.]+ (USDC|USDT)/").all()
        for element in balance_elements:
            balance_text = await element.text_content()
            match = re.search(r"Balance: ([0-9.]+) (USDC|USDT)", balance_text)
            if match:
                amount = float(match.group(1))
                token = match.group(2)
                balances[token] = amount
                print(f"检测到 {token} 余额: {amount}")
    except Exception as e:
        print(f"提取余额时出错: {e}")
        
        # 备用方法：尝试使用LLM分析结果中的余额信息
        try:
            screenshot_path = "balance_check.png"
            await page.screenshot(path=screenshot_path)
            analysis = await analyze_with_llm(screenshot_path, "请提取USDC和USDT余额")
            
            # 从分析结果中提取余额
            usdc_match = re.search(r"USDC[:\s]+([0-9.]+)", analysis)
            usdt_match = re.search(r"USDT[:\s]+([0-9.]+)", analysis)
            
            if usdc_match:
                balances["USDC"] = float(usdc_match.group(1))
            if usdt_match:
                balances["USDT"] = float(usdt_match.group(1))
        except Exception as backup_error:
            print(f"备用余额提取方法也失败: {backup_error}")
    
    return balances

async def main():
    """
    主函数：自动进行USDC和USDT之间的交易
    
    流程：
    1. 打开浏览器并访问DeFi应用
    2. 等待用户手动连接钱包
    3. 循环执行交易直到达到最大次数或成本上限
    4. 在每次交易后反转代币方向
    5. 记录交易历史并输出摘要
    """
    global total_cost
    
    # 检测是否在Docker环境中运行
    in_docker = os.path.exists('/.dockerenv')
    print(f"运行环境: {'Docker 容器' if in_docker else '本地系统'}")
    
    browser_args = []
    if in_docker:
        # Docker环境中的特殊配置
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--single-process',
            '--disable-gpu'
        ]
        print("已应用Docker特定浏览器配置")
    
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False, args=browser_args)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        # 访问DeFi应用
        await page.goto("https://app.defi.app/join/v5FvMr")
        
        # 等待加载并连接钱包
        print("请在30秒内完成钱包连接...")
        await asyncio.sleep(30)
        
        # 确保我们在交易页面
        try:
            await page.goto("https://app.defi.app/trade")
            await page.wait_for_load_state("networkidle")
        except Exception as e:
            print(f"导航到交易页面失败: {e}")
            # 如果导航失败，尝试点击Trade按钮
            try:
                await page.click("text=Trade")
                await page.wait_for_load_state("networkidle")
            except:
                print("无法进入交易页面，请手动操作")
        
        # 等待页面加载完成
        await asyncio.sleep(2.5)  # 减半：从5秒减到2.5秒
        
        # 尝试两种交易方向，先决定哪种方向有足够的余额
        has_valid_trade = False
        available_direction = None
        
        # 先尝试USDC -> USDT方向
        print("尝试查看USDC -> USDT方向是否可交易...")
        current_from_token = "USDC"
        current_to_token = "USDT"
        
        # 确保方向正确
        await ensure_swap_direction(page, current_from_token, current_to_token)
        await asyncio.sleep(1)
        
        # 尝试点击ALL看是否有余额
        try:
            # 点击ALL按钮
            all_clicked = await click_all_button(page)
            if all_clicked:
                await asyncio.sleep(1)
                
                # 获取交易成本 - 如果有余额，会显示成本
                cost = await extract_cost_from_page(page)
                if cost > 0 and cost <= MAX_COST_PER_TRADE:
                    print(f"USDC -> USDT 方向可交易，成本: {cost}")
                    has_valid_trade = True
                    available_direction = "USDC->USDT"
                else:
                    print(f"USDC -> USDT 方向不可交易，成本: {cost}")
        except Exception as e:
            print(f"测试USDC方向时出错: {e}")
        
        # 如果USDC方向不可交易，尝试USDT -> USDC
        if not has_valid_trade:
            print("尝试查看USDT -> USDC方向是否可交易...")
            current_from_token = "USDT"
            current_to_token = "USDC"
            
            # 确保方向正确
            await ensure_swap_direction(page, current_from_token, current_to_token)
            await asyncio.sleep(1)
            
            # 尝试点击ALL看是否有余额
            try:
                # 点击ALL按钮
                all_clicked = await click_all_button(page)
                if all_clicked:
                    await asyncio.sleep(1)
                    
                    # 获取交易成本 - 如果有余额，会显示成本
                    cost = await extract_cost_from_page(page)
                    if cost > 0 and cost <= MAX_COST_PER_TRADE:
                        print(f"USDT -> USDC 方向可交易，成本: {cost}")
                        has_valid_trade = True
                        available_direction = "USDT->USDC"
                    else:
                        print(f"USDT -> USDC 方向不可交易，成本: {cost}")
            except Exception as e:
                print(f"测试USDT方向时出错: {e}")
        
        # 如果两个方向都不可交易，退出程序
        if not has_valid_trade:
            print("两个交易方向都不可交易，可能没有足够余额，程序退出")
            await browser.close()
            return
        
        # 使用可交易的方向
        if available_direction == "USDC->USDT":
            current_from_token = "USDC"
            current_to_token = "USDT"
            print("使用USDC -> USDT方向开始交易")
        else:
            current_from_token = "USDT"
            current_to_token = "USDC"
            print("使用USDT -> USDC方向开始交易")
        
        # 确保初始代币方向正确
        await ensure_swap_direction(page, current_from_token, current_to_token)
        
        trade_count = 0
        last_direction_change_time = time.time()
        max_retry_same_direction = 3
        same_direction_retry = 0
        
        while trade_count < MAX_TRADES and total_cost < MAX_TOTAL_COST:
            try:
                print(f"\n--- 开始第 {trade_count+1} 次交易 ---")
                print(f"当前交易方向: {current_from_token} -> {current_to_token}")
                
                # 再次确认交易方向是否正确
                direction_correct = await ensure_swap_direction(page, current_from_token, current_to_token)
                if not direction_correct:
                    print("无法设置正确的交易方向，尝试继续...")
                
                # 截图当前状态
                screenshot_path = f"trade_status_{trade_count}.png"
                await page.screenshot(path=screenshot_path)
                
                # 先检查余额 - 分析当前截图
                current_status = f"交易次数: {trade_count}, 已消耗: {total_cost} USDT"
                analysis = await analyze_with_llm(screenshot_path, current_status)
                print(f"\n--- LLM分析 ---\n{analysis}\n")
                
                # 强制点击ALL按钮以选择最大交易额
                all_clicked = await click_all_button(page)
                
                if not all_clicked:
                    print("无法点击ALL按钮，尝试继续交易，但可能使用默认金额")
                
                # 重新获取交易成本（点击ALL后可能会改变）
                await asyncio.sleep(0.5)
                estimated_cost = await extract_cost_from_page(page)
                print(f"选择ALL后预计交易成本: {estimated_cost} USDT")
                
                # 检查是否有足够余额进行交易（通过成本判断）
                if estimated_cost <= 0 or estimated_cost > MAX_COST_PER_TRADE:
                    print(f"交易成本不合适: {estimated_cost} USDT，尝试切换方向")
                    
                    # 如果短时间内多次切换方向且仍无法交易，增加等待时间
                    current_time = time.time()
                    if current_time - last_direction_change_time < 10:
                        same_direction_retry += 1
                    else:
                        same_direction_retry = 0
                    
                    if same_direction_retry >= max_retry_same_direction:
                        print(f"多次尝试切换方向仍无法交易，等待15秒后重试")
                        await asyncio.sleep(15)
                        same_direction_retry = 0
                    
                    # 切换到另一个方向尝试
                    current_from_token, current_to_token = current_to_token, current_from_token
                    print(f"新的交易方向: {current_from_token} -> {current_to_token}")
                    last_direction_change_time = current_time
                    
                    # 确保UI反转已执行
                    if await click_reverse_button(page):
                        print(f"成功切换交易方向UI")
                        await asyncio.sleep(1)
                    else:
                        print("无法切换交易方向UI，将在下次循环中重试")
                    
                    await asyncio.sleep(WAIT_BETWEEN_TRADES)
                    continue
                
                # 重置切换方向尝试次数
                same_direction_retry = 0
                
                # 点击Swap按钮
                if await click_swap_button(page):
                    print("已点击Swap按钮")
                else:
                    print("无法点击Swap按钮，跳过此次交易")
                    await asyncio.sleep(WAIT_BETWEEN_TRADES)
                    continue
                
                # 确认交易
                if await confirm_transaction(page):
                    # 记录交易
                    transaction_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    transactions.append({
                        "time": transaction_time,
                        "from": current_from_token,
                        "to": current_to_token,
                        "cost": estimated_cost
                    })
                    
                    total_cost += estimated_cost
                    trade_count += 1
                    
                    print(f"完成交易 #{trade_count}: {current_from_token} -> {current_to_token}")
                    print(f"成本: {estimated_cost} USDT, 总消耗: {total_cost} USDT")
                    
                    # 等待交易完成，确保页面更新
                    await page.wait_for_load_state("networkidle", timeout=30000)
                    await asyncio.sleep(2.5)
                    
                    # 交易完成后交换From和To代币（为下一次交易做准备）
                    # 注意：先交换变量，再点击反转按钮
                    old_from = current_from_token
                    old_to = current_to_token
                    current_from_token, current_to_token = current_to_token, current_from_token
                    print(f"交易完成，切换交易方向为: {current_from_token} -> {current_to_token}")
                    
                    # 交易完成后一定要点击反转按钮，这是关键步骤，多次尝试确保成功
                    print(f"正在将交易方向从 {old_from}->{old_to} 反转为 {current_from_token}->{current_to_token}")
                    
                    # 强制点击反转按钮，多次尝试确保成功
                    reverse_success = False
                    for retry in range(5):  # 最多尝试5次
                        if await click_reverse_button(page):
                            print(f"第{retry+1}次尝试: 已点击反转按钮准备下一次交易")
                            reverse_success = True
                            await asyncio.sleep(1)
                            break
                        else:
                            print(f"第{retry+1}次尝试: 点击反转按钮失败，等待后重试")
                            await asyncio.sleep(1)
                    
                    if not reverse_success:
                        print("警告: 无法点击反转按钮，将在下一次交易前重新确认方向")
                    
                    # 休息一段时间，避免操作过快
                    await asyncio.sleep(WAIT_BETWEEN_TRADES)
                else:
                    print("交易可能未成功完成，等待后重试")
                    await asyncio.sleep(WAIT_BETWEEN_TRADES)
            
            except Exception as e:
                print(f"交易过程中出现错误: {e}")
                await asyncio.sleep(2.5)
        
        # 交易结束，打印摘要
        print("\n--- 交易摘要 ---")
        print(f"总交易次数: {trade_count}")
        print(f"总消耗USDT: {total_cost}")
        print("交易记录:")
        for tx in transactions:
            print(f"{tx['time']}: {tx['from']} -> {tx['to']}, 成本: {tx['cost']} USDT")
        
        # 关闭浏览器
        await browser.close()

async def click_all_button(page):
    """尝试点击ALL按钮选择最大交易额"""
    try:
        # 尝试多种方式点击ALL按钮
        selectors = [
            'button:has-text("ALL")',
            'button.border.border-border-secondary:has(span:text("ALL"))',
            'button:has(span:text("ALL"))',
            'button:has-text("MAX")',  # 有些界面可能使用MAX而不是ALL
        ]
        
        for selector in selectors:
            try:
                await page.click(selector)
                print(f"使用选择器 '{selector}' 成功点击ALL按钮")
                await page.wait_for_timeout(1000)
                return True
            except Exception:
                continue
        
        # 使用JavaScript尝试点击
        all_clicked = await page.evaluate('''
            (() => {
                // 尝试各种可能的选择器
                const selectors = [
                    'button:has-text("ALL")',
                    'button.border',
                    'span:has-text("ALL")',
                    'button:has-text("MAX")'
                ];
                
                for (const selector of selectors) {
                    const buttons = document.querySelectorAll(selector);
                    for (const button of buttons) {
                        if (button.textContent.includes('ALL') || button.textContent.includes('MAX')) {
                            button.click();
                            return true;
                        }
                    }
                }
                
                return false;
            })()
        ''')
        if all_clicked:
            print("使用JavaScript成功点击ALL按钮")
            await page.wait_for_timeout(1000)
            return True
        
        print("无法点击ALL按钮")
        return False
    except Exception as e:
        print(f"尝试点击ALL按钮时出错: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())