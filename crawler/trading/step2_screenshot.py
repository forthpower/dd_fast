"""步骤 2: 进入网站截图并裁切"""
import os
import json
import time
from datetime import datetime
from pathlib import Path
import requests
from PIL import Image
from selenium import webdriver
import pandas as pd

EXCEL_FILE = os.path.join(os.path.dirname(__file__), "crypto.xlsx")
EXCEL_SHEET = "Strategy Watchlist"
CROP_COORDS = (0.6,0.7,1.0,0.94)
BASE_DIR = os.path.dirname(__file__)
COOKIE_FILE = os.path.join(BASE_DIR, "cookies.json")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "result/screenshots")
CROPPED_DIR = os.path.join(BASE_DIR, "result/cropped")


def load_urls():
    try:
        df = pd.read_excel(EXCEL_FILE, sheet_name=EXCEL_SHEET)
        urls = [u.strip() for u in df.iloc[:, -1].dropna().astype(str) if u.strip().startswith('http')]
        return list(dict.fromkeys(urls))
    except Exception as e:
        print(f"❌ 读取 Excel 失败：{e}")
        return []


def load_cookie():
    with open(COOKIE_FILE, 'r', encoding='utf-8') as f:
        cookies = json.load(f)
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})
    for c in cookies:
        session.cookies.set(name=c.get("name"), value=c.get("value"), domain=c.get("domain"), path=c.get("path", "/"))
    return session


def inject_cookies(driver, session):
    driver.get("https://www.tradingview.com")
    time.sleep(10)
    cdp = driver.execute_cdp_cmd
    for cookie in session.cookies:
        try:
            domain = cookie.domain or ".tradingview.com"
            if 'www.' in domain:
                domain = domain.replace('www.', '')
            if not domain.startswith('.'):
                domain = f".{domain}"
            cdp("Network.setCookie", {
                "name": cookie.name, "value": cookie.value, "domain": domain, "path": cookie.path or "/",
                "secure": getattr(cookie, 'secure', False), "httpOnly": getattr(cookie, 'httpOnly', False)
            })
        except:
            pass
    driver.refresh()


def screenshot_and_crop():
    session = load_cookie()
    urls = load_urls()
    print(f"✅ 加载 {len(urls)} 个 URL")
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
    
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.execute_cdp_cmd("Network.enable", {})
    inject_cookies(driver, session)
    
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
    os.makedirs(CROPPED_DIR, exist_ok=True)
    
    for idx, url in enumerate(urls, 1):
        print(f"[{idx}/{len(urls)}] {url}")
        driver.get(url)
        time.sleep(60)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        url_part = url.split("/")[-2] if "/" in url else "tradingview"
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"tradingview_{url_part}_{timestamp}.png")
        
        try:
            driver.save_screenshot(screenshot_path)
            print(f"✅ {Path(screenshot_path).name}")
        except Exception as e:
            print(f"❌ 失败：{e}")
    
    driver.quit()
    print(f"\n✅ 完成：截图 {len(urls)} 张")
    crop()


def crop():
    print("\n✂️ 裁切图片...")
    left, top, right, bottom = CROP_COORDS
    files = [os.path.join(SCREENSHOTS_DIR, f) for f in os.listdir(SCREENSHOTS_DIR) 
             if os.path.isfile(os.path.join(SCREENSHOTS_DIR, f)) and f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    for path in files:
        try:
            img = Image.open(path)
            left_crop = int(img.width * left)
            top_crop = int(img.height * top)
            right_crop = int(img.width * right)
            bottom_crop = int(img.height * bottom)
            Image.open(path).crop((left_crop, top_crop, right_crop, bottom_crop)).save(
                os.path.join(CROPPED_DIR, f"{Path(path).stem}_cropped{Path(path).suffix}"))
            print(f"✅ {Path(path).name}")
        except Exception as e:
            print(f"❌ {Path(path).name}: {e}")
    
    print(f"\n✅ 完成：裁切 {len(files)} 张")


if __name__ == "__main__":
    screenshot_and_crop()
    # crop()
