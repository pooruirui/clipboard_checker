import asyncio
import base64
import os
import sys
import requests
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from typing import Optional

async def extract_qr_code(page: Page, qr_selector: str, timeout: int = 60000) -> Optional[str]:
    """
    提取二维码图片的 Base64 编码或下载二维码图片并返回其内容。

    :param page: Playwright 页面对象
    :param qr_selector: 用于定位二维码图片的选择器（XPath 或 CSS 选择器）
    :param timeout: 等待二维码出现的超时时间（毫秒）
    :return: 二维码图片的 Base64 编码字符串，或 None 表示提取失败
    """
    try:
        print(f"等待二维码元素出现，选择器: {qr_selector}，超时时间: {timeout / 1000}秒")
        # 等待二维码元素出现，最多等待 timeout 毫秒
        qr_element = await page.wait_for_selector(qr_selector, timeout=timeout)
        print("找到二维码元素。")

        # 获取二维码的 src 属性
        qr_src = await qr_element.get_attribute("src")
        if not qr_src:
            print("二维码的 src 属性为空。")
            return None

        # 判断 src 是 data URL 还是普通 URL
        if qr_src.startswith("data:image"):
            # Data URL，直接提取 Base64 编码
            _, encoded = qr_src.split(",", 1)
            return encoded
        else:
            # 普通 URL，下载图片并转换为 Base64 编码
            print(f"二维码图片的 src 是普通 URL: {qr_src}")
            response = requests.get(qr_src)
            if response.status_code == 200:
                encoded = base64.b64encode(response.content).decode()
                return encoded
            else:
                print(f"下载二维码图片失败，状态码：{response.status_code}")
                return None
    except Exception as e:
        print(f"提取二维码时发生错误：{e}")
        return None

def save_qr_code(base64_qr: str, file_path: str = "qr_code.png"):
    """
    将 Base64 编码的二维码图片保存为本地文件。

    :param base64_qr: 二维码图片的 Base64 编码
    :param file_path: 保存的文件路径
    """
    try:
        img_data = base64.b64decode(base64_qr)
        with open(file_path, "wb") as f:
            f.write(img_data)
        print(f"二维码已保存为 {file_path}。")

        # 打开图片文件，使用默认图片查看器
        if os.name == 'nt':  # Windows
            os.startfile(file_path)
        elif os.name == 'posix':
            import subprocess
            subprocess.run(["open", file_path])
        else:
            print("请手动打开 qr_code.png 以扫描二维码。")
    except Exception as e:
        print(f"保存二维码图片时发生错误：{e}")

async def check_login_state(context: BrowserContext, initial_web_session: Optional[str] = None, retries: int = 120, interval: int = 1) -> Optional[str]:
    """
    检查登录状态，通过比较 'web_session' Cookie 是否发生变化来判断是否登录成功。

    :param context: Playwright 浏览器上下文
    :param initial_web_session: 登录前的 'web_session' Cookie 值
    :param retries: 重试次数
    :param interval: 重试间隔（秒）
    :return: 新的 'web_session' Cookie 值，或 None 表示未检测到登录成功
    """
    for attempt in range(retries):
        cookies = await context.cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        current_web_session = cookie_dict.get("web_session")
        if initial_web_session is None:
            if current_web_session:
                print("检测到 'web_session' Cookie，登录可能已成功。")
                return current_web_session
        else:
            if current_web_session and current_web_session != initial_web_session:
                print("检测到 'web_session' Cookie 已更新，登录成功。")
                return current_web_session
        print(f"等待登录完成... ({attempt + 1}/{retries})")
        await asyncio.sleep(interval)
    print("登录超时，未检测到登录成功。")
    return None

async def main():
    async with async_playwright() as p:
        # 启动浏览器，无头模式
        print("启动无头浏览器...")
        browser: Browser = await p.chromium.launch(
            executable_path="chrome-win/chrome.exe",  # 指定浏览器可执行文件路径
            headless=False,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-blink-features=AutomationControlled"
            ],
            ignore_default_args=["--enable-automation"]
        )
        context: BrowserContext = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        )
        page: Page = await context.new_page()

        # 注入脚本以隐藏自动化特征
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.navigator.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
        """)

        # 导航到小红书探索页面
        target_url = "https://www.xiaohongshu.com/explore"
        print(f"导航到 {target_url}...")
        await page.goto(target_url)

        # 定义二维码的选择器
        # 根据您提供的 XPath 路径，这里使用绝对 XPath，但建议尽量使用更稳健的选择器
        # 您可以根据实际页面结构调整选择器
        qr_xpath = "/html/body/div[1]/div[1]/div/div[1]/div[2]/div[2]/div[2]/img"
        qr_selector = f"xpath={qr_xpath}"
        # 或者使用相对 XPath 或 CSS 选择器，例如：
        # qr_selector = "img.qrcode-img"

        # 提取二维码图片
        print("提取二维码图片...")
        base64_qr = await extract_qr_code(page, qr_selector, timeout=120000)  # 设置超时时间为120秒
        if not base64_qr:
            print("二维码提取失败，退出程序。")
            await browser.close()
            sys.exit(1)

        # 保存二维码图片并打开
        print("保存二维码图片并打开...")
        save_qr_code(base64_qr, "qr_code.png")

        # 提醒用户扫码
        print("请使用手机扫描 'qr_code.png' 中的二维码以登录。")

        # 获取登录前的 'web_session' Cookie 值
        cookies = await context.cookies()
        cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
        initial_web_session = cookie_dict.get("web_session")
        print(f"初始 'web_session' Cookie: {initial_web_session}")

        # 等待用户扫码并登录
        print("等待用户扫码并完成登录...")
        new_web_session = await check_login_state(context, initial_web_session, retries=120, interval=1)  # 等待最多120秒

        if new_web_session:
            print(f"登录成功。'web_session' Cookie: {new_web_session}")
            # 打开文件，如果文件不存在则创建，如果存在则覆盖
            with open('websession.txt', 'w') as file:
                # 将 web_session 的内容写入文件
                file.write(str(new_web_session))
        else:
            print("登录未完成或超时。")

        # 关闭浏览器
        print("关闭浏览器。")
        await browser.close()

        # 关闭打开的二维码图片
        if os.name == 'nt':
            # Windows 不支持直接关闭打开的文件，需使用第三方库或手动关闭
            print("请手动关闭 'qr_code.png'。")
        elif os.name == 'posix':
            # macOS 使用 'open' 命令打开的文件无法通过 subprocess 关闭
            # 可以考虑使用其他方法，如通过 PID 管理打开的进程
            print("请手动关闭 'qr_code.png'。")
        else:
            print("请手动关闭 'qr_code.png'。")

if __name__ == "__main__":
    asyncio.run(main())
