
from selenium import webdriver
from selenium.webdriver.common.by import By
import ddddocr
import time
import os
import traceback
import concurrent.futures

# --- Rich 导入 ---
from rich.console import Console
from rich.panel import Panel
# --- Rich 导入 ---

# --- 配置 ---
REFRESH_WAIT_TIME = 3           # 标准刷新后的等待时间
SUBMIT_WAIT_TIME = 1            # 提交后等待确认的时间
INITIAL_LOAD_WAIT = 2           # 初始加载后等待多久开始检查
MAX_ELEMENT_WAIT = 30           # 等待关键元素出现的最大时间
OCR_RETRY_WAIT_TIME = 5         # OCR识别失败后的额外等待时间
CONTRIBUTOR_NAME = "liyifan202201" # 贡献者名称
# --- 配置 ---

# --- Rich Console 实例 (自动适应终端大小) ---
console = Console()
# --- Rich Console 实例 ---

# 初始化 ddddocr 识别器 (使用 beta 模型可能效果更好)
ocr = ddddocr.DdddOcr(beta=True,show_ad=False)

# 初始化 Edge 浏览器
def init_driver():
    options = webdriver.EdgeOptions()
    options.add_experimental_option('excludeSwitches', ['enable-logging'])
    options.add_argument("--start-maximized")
    # --- 关键优化 ---
    # 设置页面加载策略为 'none' 可以让 navigation 完成后 driver.get() 立即返回
    # 这样我们可以更快地开始检查元素，即使页面还在后台加载
    options.page_load_strategy = 'none'
    driver = webdriver.Edge(options=options)
    # 设置一个合理的超时，以防万一 get() 挂起
    driver.set_page_load_timeout(60)
    return driver

# 识别验证码
def recognize_captcha(driver):
    try:
        captcha_img = driver.find_element(By.CSS_SELECTOR, "#captcha_img")
    except Exception as e:
        console.log("[red][OCR][/red] 未找到验证码图片元素", style="bold red")
        # console.log(f"[red][OCR Detail][/red] {e}", style="dim") # 可选：打印详细错误
        return ""

    current_dir = os.getcwd()
    screenshot_path = os.path.join(current_dir, "captcha_screenshot.png")

    try:
        captcha_img.screenshot(screenshot_path)
    except Exception as e:
        console.log("[red][OCR][/red] 截图失败", style="bold red")
        # console.log(f"[red][OCR Detail][/red] {e}", style="dim")
        return ""

    if not os.path.exists(screenshot_path):
        console.log("[red][OCR][/red] 验证码图片保存失败", style="bold red")
        return ""

    try:
        with open(screenshot_path, "rb") as f:
            image = f.read()
        captcha_text = ocr.classification(image)
        console.log(f"[green][OCR][/green] 识别结果: [bold]{captcha_text}[/bold]", style="green")
        return captcha_text
    except Exception as e:
        console.log("[red][OCR][/red] 读取或识别图片时出错", style="bold red")
        # console.log(f"[red][OCR Detail][/red] {e}", style="dim")
        return ""

# --- 修改后的处理验证码函数 ---
def handle_captcha(driver):
    captcha_url = "https://vjudge.net/util/luogu/captcha"

    # 定义检查元素是否存在的辅助函数
    def is_element_present(by, value):
        try:
            driver.find_element(by, value)
            return True
        except:
            return False

    console.print(Panel(f"[bold blue]开始加载页面:[/bold blue] {captcha_url}", title="初始化", expand=False))

    # 使用线程池控制 driver.get 并行检查元素
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(driver.get, captcha_url)

        time.sleep(INITIAL_LOAD_WAIT)
        console.log(f"[yellow][INIT][/yellow] 等待 {INITIAL_LOAD_WAIT}s 后开始检查关键元素...")

        start_check_time = time.time()
        while time.time() - start_check_time < MAX_ELEMENT_WAIT:
            # 检查一个关键的、较早出现的元素，如导航栏中的链接
            # 注意：原始HTML片段显示的元素可能不完全准确，这里沿用之前的逻辑
            # 如果发现始终超时，可能需要调整此XPath
            if is_element_present(By.XPATH, '//*[@id="navbarResponsive"]//a'):
                console.log("[green][INIT][/green] 关键元素已加载，准备开始处理。", style="bold green")
                # 不等待 driver.get 完全结束，因为我们已经可以操作了
                break
            else:
                console.log("[yellow][INIT][/yellow] ... 等待关键元素出现 ...", style="dim")
                time.sleep(1)
        else:
            console.log(f"[red][INIT][/red] 致命错误：等待关键元素超时 ({MAX_ELEMENT_WAIT}s)。", style="bold red")
            # 可以选择在此处返回或抛出异常
            return # 或 raise Exception("页面加载超时")

    console.print(Panel("[bold green]页面加载检查通过，进入主循环...[/bold green]", title="主循环开始", expand=False))

    # --- 主验证码处理循环 ---
    loop_count = 0
    while True:
        loop_count += 1
        console.print(Panel(f"[bold blue]开始新一轮验证码处理 (第 {loop_count} 轮)[/bold blue]", title="循环", expand=False))

        try:
            # --- 1. 等待并获取验证码图片 ---
            captcha_img = None
            for attempt in range(5):
                try:
                    captcha_img = driver.find_element(By.CSS_SELECTOR, "#captcha_img")
                    if captcha_img:
                        break
                except:
                    pass
                if attempt < 4: # 避免最后一次不必要的日志
                    console.log(f"[yellow][CAPTCHA][/yellow] 等待验证码图片加载 (尝试 {attempt + 1}/5)...", style="dim")
                time.sleep(1)

            if not captcha_img:
                console.log("[red][CAPTCHA][/red] 未找到验证码图片，刷新重试...", style="bold red")
                driver.refresh()
                time.sleep(REFRESH_WAIT_TIME)
                continue

            img_src = captcha_img.get_attribute("src")
            # 简化日志输出
            # console.log(f"[cyan][CAPTCHA][/cyan] 图片src: {img_src}")

            # 检查图片是否有效加载 (检查 src 是否不是占位符)
            if not img_src or img_src.endswith("#") or img_src in ("data:,", ","):
                console.log("[yellow][CAPTCHA][/yellow] 图片未加载 (src 是占位符)，刷新重试...", style="bold yellow")
                driver.refresh()
                time.sleep(REFRESH_WAIT_TIME)
                continue

            # --- 2. 识别验证码 ---
            captcha_text_raw = recognize_captcha(driver)

            # 处理识别结果
            captcha_text = ""
            if captcha_text_raw:
                captcha_text = captcha_text_raw.replace(" ", "")
                captcha_text = ''.join(filter(str.isalnum, captcha_text)).lower()

            console.log(f"[magenta][OCR][/magenta] 处理后识别结果: [bold]{captcha_text}[/bold]")

            if not captcha_text or len(captcha_text) != 5:
                console.log(f"[red][OCR][/red] 识别失败或长度不合适 (!=5)，等待 {OCR_RETRY_WAIT_TIME}s 后刷新重试...", style="bold red")
                # --- 关键修改：识别失败后增加等待时间 ---
                time.sleep(OCR_RETRY_WAIT_TIME)
                # -----------------------------------
                driver.refresh()
                time.sleep(REFRESH_WAIT_TIME)
                continue

            # --- 3. 填写表单 ---
            # 输入验证码
            captcha_input = None
            for _ in range(5):
                try:
                    captcha_input = driver.find_element(By.CSS_SELECTOR, "#captcha_form > label:nth-child(4) > input")
                    if captcha_input:
                        break
                except:
                    pass
                time.sleep(0.5)
            if not captcha_input:
                 raise Exception("未找到验证码输入框")

            captcha_input.clear()
            captcha_input.send_keys(captcha_text)
            console.log("[green][FORM][/green] 验证码已输入", style="green")

            # 输入贡献者名称
            contributor_input = None
            for _ in range(5):
                try:
                   contributor_input = driver.find_element(By.CSS_SELECTOR, "#contributor_name > input")
                   if contributor_input:
                        break
                except:
                    pass
                time.sleep(0.5)
            if not contributor_input:
                 raise Exception("未找到贡献者名称输入框")

            contributor_input.clear()
            contributor_input.send_keys(CONTRIBUTOR_NAME)
            console.log(f"[green][FORM][/green] 贡献者名称 ({CONTRIBUTOR_NAME}) 已输入", style="green")

            # --- 4. 提交表单 ---
            submit_btn = None
            for _ in range(5):
                try:
                   submit_btn = driver.find_element(By.CSS_SELECTOR, "#captcha_form > input[type=submit]:nth-child(5)")
                   if submit_btn:
                        break
                except:
                    pass
                time.sleep(0.5)
            if not submit_btn:
                 raise Exception("未找到提交按钮")

            submit_btn.click()
            console.log("[green][SUBMIT][/green] 已提交表单", style="bold green")

            # 等待一小段时间确认提交
            time.sleep(SUBMIT_WAIT_TIME)
            console.log("[green][SUBMIT][/green] 提交完成", style="green")

            # --- 5. 立即刷新，开始下一轮 ---
            console.log("[blue][REFRESH][/blue] 立即刷新页面...")
            driver.refresh()
            console.log(f"[blue][REFRESH][/blue] 已刷新，等待 {REFRESH_WAIT_TIME}s...")
            time.sleep(REFRESH_WAIT_TIME)

        except Exception as e:
            console.log(f"[red][ERROR][/red] 发生错误: {e}", style="bold red on black")
            # console.print_exception() # 可根据需要开启详细堆栈

            # 出错时的恢复逻辑
            try:
                console.log("[yellow][RECOVER][/yellow] 尝试刷新页面恢复...")
                time.sleep(1)
                driver.refresh()
                console.log(f"[yellow][RECOVER][/yellow] 已刷新，等待 {REFRESH_WAIT_TIME}s...")
                time.sleep(REFRESH_WAIT_TIME)
            except Exception as refresh_e:
                console.log(f"[red][RECOVER][/red] 刷新失败: {refresh_e}", style="red")
                try:
                    console.log("[red][RECOVER][/red] 尝试重新打开页面...")
                    time.sleep(1)
                    driver.get(captcha_url)
                    console.log(f"[red][RECOVER][/red] 已重新打开，等待 {REFRESH_WAIT_TIME}s...")
                    time.sleep(REFRESH_WAIT_TIME)
                except Exception as reopen_e:
                    console.log(f"[red][RECOVER][/red] 重新打开页面也失败: {reopen_e}", style="red")
                    console.log("[yellow][RECOVER][/yellow] 继续下一轮循环...")

def main():
    driver = init_driver()
    driver.implicitly_wait(5) # 设置较短的隐式等待，用于 find_element
    try:
        console.print(Panel("[bold green]脚本启动成功[/bold green]", title="启动", expand=False))
        handle_captcha(driver)
    except Exception as e:
        console.log(f"[red][MAIN][/red] 程序出错: {e}", style="bold red on black")
        console.print_exception()
    finally:
        console.input("[bold yellow]程序结束，按 Enter 退出...[/bold yellow]")
        driver.quit()

if __name__ == "__main__":
    main()
