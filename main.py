import asyncio
import os
from datetime import datetime

# --- Playwright 导入 ---
from playwright.async_api import async_playwright, Page, Locator, TimeoutError as PlaywrightTimeoutError
# --- Playwright 导入 ---

# --- Rich 导入 ---
from rich.console import Console
from rich.panel import Panel
# --- Rich 导入 ---

# --- ddddocr 导入 ---
import ddddocr # 确保已安装 ddddocr
# --- ddddocr 导入 ---

# --- 配置 ---
REFRESH_WAIT_TIME = 3           # 标准刷新后的等待时间 (秒)
SUBMIT_WAIT_TIME = 1            # 提交后等待确认的时间 (秒)
INITIAL_LOAD_WAIT = 1           # 初始加载后等待多久开始检查 (秒)
MAX_ELEMENT_WAIT = 30           # 等待关键元素出现的最大时间 (秒)
OCR_RETRY_WAIT_TIME = 3         # OCR识别失败后的额外等待时间 (秒)
CONTRIBUTOR_NAME = "liyifan202201-bot"           # 贡献者名称
CAPTCHA_URL = "https://vjudge.net/util/luogu/captcha"
# --- 配置 ---

# --- Rich Console 实例 ---
console = Console()
# --- Rich Console 实例 ---

# 初始化 ddddocr 识别器
ocr = ddddocr.DdddOcr(beta=True, show_ad=False)

# --- 辅助函数 ---

def log_with_timestamp(message: str, style: str = ""):
    """为日志消息添加时间戳"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = f"[{timestamp}]"
    console.log(prefix, message, style=style)

# --- Playwright 辅助函数 ---

async def wait_for_element(page: Page, selector: str, timeout: int = MAX_ELEMENT_WAIT) -> bool:
    """等待元素出现"""
    try:
        await page.wait_for_selector(selector, state="attached", timeout=timeout * 1000)
        return True
    except PlaywrightTimeoutError:
        return False

async def wait_for_image_loaded(img_locator: Locator, timeout: int = 10) -> bool:
    """
    等待图片加载完成。
    通过检查图片的 src 属性并在页面上监听对应的 response 来判断。
    """
    try:
        img_src = await img_locator.get_attribute('src')
        if not img_src:
            return False

        async with img_locator.page.expect_response(
            lambda response: response.url == img_src and response.status == 200,
            timeout=timeout * 1000
        ):
            pass
        return True
    except (PlaywrightTimeoutError, Exception):
        return False

# --- 核心逻辑函数 ---

async def recognize_captcha(page: Page) -> str:
    """识别验证码"""
    try:
        captcha_img_locator = page.locator("#captcha_img")
        
        # 等待图片元素出现
        if not await wait_for_element(page, "#captcha_img"):
             log_with_timestamp("[red][OCR][/red] 未找到验证码图片元素", style="bold red")
             return ""

        # 等待图片加载完成 (可选，但更健壮)
        # await wait_for_image_loaded(captcha_img_locator)

        screenshot_path = f"captcha_screenshot.png"
        
        # 截图验证码元素
        await captcha_img_locator.screenshot(path=screenshot_path, type="png")

        if not os.path.exists(screenshot_path):
            log_with_timestamp("[red][OCR][/red] 验证码图片保存失败", style="bold red")
            return ""

        # 使用 ddddocr 识别 (同步调用)
        try:
            with open(screenshot_path, "rb") as f:
                image = f.read()
            captcha_text = ocr.classification(image)
            log_with_timestamp(f"[green][OCR][/green] 识别结果: [bold]{captcha_text}[/bold]", style="green")
            return captcha_text
        except Exception as e:
            log_with_timestamp(f"[red][OCR][/red] 读取或识别图片时出错: {e}", style="bold red")
            return ""
        finally:
            # 清理临时截图
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)

    except Exception as e:
        log_with_timestamp(f"[red][OCR][/red] 截图或查找图片时出错: {e}", style="bold red")
        return ""

async def process_captcha_loop(page: Page):
    """主验证码处理循环"""
    loop_count = 0
    
    # 初始加载页面
    log_with_timestamp(Panel(f"[bold blue]开始加载页面:[/bold blue] {CAPTCHA_URL}", title="初始化", expand=False))
    await page.goto(CAPTCHA_URL, wait_until='domcontentloaded') # 关键：快速加载
    
    # 等待初始加载
    await asyncio.sleep(INITIAL_LOAD_WAIT) 
    log_with_timestamp(f"[yellow][INIT][/yellow] 等待 {INITIAL_LOAD_WAIT}s 后开始检查验证码元素...", style="dim")

    # 等待验证码图片元素出现
    if not await wait_for_element(page, "#captcha_img", timeout=MAX_ELEMENT_WAIT):
        log_with_timestamp(f"[red][INIT][/red] 致命错误：等待验证码图片超时 ({MAX_ELEMENT_WAIT}s)。", style="bold red")
        return

    log_with_timestamp(Panel("[bold green]验证码元素已找到，进入主循环...[/bold green]", title="主循环开始", expand=False))

    # 获取初始验证码图片的 src 用于后续比较
    initial_captcha_src = await page.locator("#captcha_img").get_attribute("src")
    last_captcha_src = initial_captcha_src

    while True:
        loop_count += 1
        log_with_timestamp(Panel(f"[bold blue]开始新一轮验证码处理 (第 {loop_count} 轮)[/bold blue]", title="循环", expand=False))

        try:
            # --- 1. 等待并获取验证码图片 ---
            captcha_img_locator = page.locator("#captcha_img")
            
            # 等待图片元素存在
            if not await wait_for_element(page, "#captcha_img"):
                log_with_timestamp("[red][CAPTCHA][/red] 未找到验证码图片，刷新重试...", style="bold red")
                await page.reload(wait_until='domcontentloaded')
                await asyncio.sleep(REFRESH_WAIT_TIME)
                continue

            # 等待图片加载完成
            # if not await wait_for_image_loaded(captcha_img_locator, timeout=5):
            #      log_with_timestamp("[yellow][CAPTCHA][/yellow] 图片未加载完成，刷新重试...", style="bold yellow")
            #      await page.reload(wait_until='domcontentloaded')
            #      await asyncio.sleep(REFRESH_WAIT_TIME)
            #      continue

            img_src = await captcha_img_locator.get_attribute("src")
            
            # 检查图片是否有效加载
            if not img_src or img_src.endswith("#") or img_src in ("data:,", ","):
                log_with_timestamp("[yellow][CAPTCHA][/yellow] 图片 src 无效，刷新重试...", style="bold yellow")
                await page.reload(wait_until='domcontentloaded')
                await asyncio.sleep(REFRESH_WAIT_TIME)
                continue

            # --- 2. 识别验证码 ---
            captcha_text_raw = await recognize_captcha(page)
            captcha_text = ""
            if captcha_text_raw:
                captcha_text = captcha_text_raw.replace(" ", "")
                captcha_text = ''.join(filter(str.isalnum, captcha_text)).lower()
            
            log_with_timestamp(f"[magenta][OCR][/magenta] 处理后识别结果: [bold]{captcha_text}[/bold]")
            
            if not captcha_text or len(captcha_text) != 4:
                log_with_timestamp(f"[red][OCR][/red] 识别失败或长度不合适 (!=4)，等待 {OCR_RETRY_WAIT_TIME}s 后刷新重试...", style="bold red")
                await asyncio.sleep(OCR_RETRY_WAIT_TIME)
                await page.reload(wait_until='domcontentloaded')
                await asyncio.sleep(REFRESH_WAIT_TIME)
                continue

            # --- 3. 填写表单 ---
            # 输入验证码
            captcha_input_locator = page.locator("#captcha_form > label:nth-child(4) > input")
            try:
                await captcha_input_locator.wait_for(state="visible", timeout=5000)
                await captcha_input_locator.fill(captcha_text)
                log_with_timestamp("[green][FORM][/green] 验证码已输入", style="green")
            except Exception as e:
                log_with_timestamp(f"[red][FORM][/red] 填写验证码失败: {e}", style="bold red")
                raise

            # 输入贡献者名称
            contributor_input_locator = page.locator("#contributor_name > input")
            try:
                await contributor_input_locator.wait_for(state="visible", timeout=5000)
                await contributor_input_locator.fill(CONTRIBUTOR_NAME)
                log_with_timestamp(f"[green][FORM][/green] 贡献者名称 ({CONTRIBUTOR_NAME}) 已输入", style="green")
            except Exception as e:
                log_with_timestamp(f"[red][FORM][/red] 填写贡献者名称失败: {e}", style="bold red")
                raise

            # --- 4. 提交表单 ---
            submit_btn_locator = page.locator("#captcha_form > input[type=submit]:nth-child(5)")
            try:
                await submit_btn_locator.wait_for(state="visible", timeout=5000)
                await submit_btn_locator.click()
                log_with_timestamp("[green][SUBMIT][/green] 已提交表单", style="bold green")
                
                # 等待一小段时间确认提交
                await asyncio.sleep(SUBMIT_WAIT_TIME) 
                log_with_timestamp("[green][SUBMIT][/green] 提交完成", style="green")
                
            except Exception as e:
                log_with_timestamp(f"[red][SUBMIT][/red] 提交表单失败: {e}", style="bold red")
                raise

            # --- 5. 检查验证码是否更新 (新要求) ---
            log_with_timestamp("[blue][CHECK][/blue] 检查验证码是否已更新...", style="blue")
            
            # 等待一小段时间让服务器可能返回新验证码
            await asyncio.sleep(1) 
            
            # 重新获取验证码图片的 src
            try:
                new_captcha_img_locator = page.locator("#captcha_img")
                # 等待元素稳定 (可选)
                # await new_captcha_img_locator.wait_for(state="visible", timeout=2000)
                new_img_src = await new_captcha_img_locator.get_attribute("src")
                
                # 判断是否是新的有效验证码
                if new_img_src and new_img_src != img_src and not new_img_src.endswith("#") and new_img_src not in ("data:,", ","):
                    log_with_timestamp("[green][CHECK][/green] 检测到新的验证码，继续处理...", style="bold green")
                    last_captcha_src = new_img_src # 更新记录
                    # 不刷新，直接进入下一轮循环
                    continue 
                else:
                    log_with_timestamp("[yellow][CHECK][/yellow] 未检测到新验证码或新验证码无效，执行刷新...", style="yellow")
            except Exception as e:
                log_with_timestamp(f"[yellow][CHECK][/yellow] 检查新验证码时出错: {e}, 执行刷新...", style="yellow")
            
            # 如果没有检测到新验证码或出错，则刷新
            log_with_timestamp("[blue][REFRESH][/blue] 刷新页面...")
            await page.reload(wait_until='domcontentloaded') # 关键：快速加载
            log_with_timestamp(f"[blue][REFRESH][/blue] 已刷新，等待 {REFRESH_WAIT_TIME}s...")
            await asyncio.sleep(REFRESH_WAIT_TIME)

        except PlaywrightTimeoutError as te:
             log_with_timestamp(f"[red][ERROR][/red] Playwright 超时: {te}", style="bold red on black")
             log_with_timestamp("[yellow][RECOVER][/yellow] 尝试刷新页面恢复...", style="yellow")
             await page.reload(wait_until='domcontentloaded')
             await asyncio.sleep(REFRESH_WAIT_TIME)
        except Exception as e:
            log_with_timestamp(f"[red][ERROR][/red] 发生错误: {e}", style="bold red on black")
            # console.print_exception() # 可根据需要开启详细堆栈

            # 出错时的恢复逻辑 - 简单刷新
            try:
                log_with_timestamp("[yellow][RECOVER][/yellow] 尝试刷新页面恢复...", style="yellow")
                await asyncio.sleep(1)
                await page.reload(wait_until='domcontentloaded') # 关键：快速加载
                log_with_timestamp(f"[yellow][RECOVER][/yellow] 已刷新，等待 {REFRESH_WAIT_TIME}s...")
                await asyncio.sleep(REFRESH_WAIT_TIME)
            except Exception as refresh_e:
                log_with_timestamp(f"[red][RECOVER][/red] 刷新失败: {refresh_e}", style="red")
                log_with_timestamp("[yellow][RECOVER][/yellow] 继续下一轮循环...", style="yellow")
                await asyncio.sleep(REFRESH_WAIT_TIME) # 即使恢复失败也等待后继续

async def main():
    console.print(Panel("[bold green]Playwright 脚本启动成功[/bold green]", title="启动", expand=False))
    
    async with async_playwright() as p:
        # 启动浏览器 (这里以 Chromium 为例)
        browser = await p.chromium.launch(
            headless=True, # 设置为 True 可以无头运行
            args=["--start-maximized"]
        )
        
        # 创建浏览器上下文和页面
        context = await browser.new_context()
        page = await context.new_page()
        
        # 设置较长的默认超时
        page.set_default_timeout(30000) # 30秒

        try:
            # 进入主处理循环
            await process_captcha_loop(page)

        except KeyboardInterrupt:
            log_with_timestamp("[yellow][MAIN][/yellow] 收到 KeyboardInterrupt，正在退出...", style="bold yellow")
        except Exception as e:
            log_with_timestamp(f"[red][MAIN][/red] 主循环中发生错误: {e}", style="bold red")
            # console.print_exception()
        finally:
            await page.close()
            await context.close()
            await browser.close()
            log_with_timestamp("[bold green]浏览器已关闭。[/bold green]")

    console.input("[bold yellow]程序结束，按 Enter 退出...[/bold yellow]")

if __name__ == "__main__":
    asyncio.run(main())
