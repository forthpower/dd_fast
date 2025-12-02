"""步骤 1: 手动登录 TradingView 并保存 cookie"""
import os
import json
import requests
from selenium import webdriver

LOGIN_URL = "https://www.tradingview.com/accounts/signin/"
COOKIE_FILE = os.path.join(os.path.dirname(__file__), "cookies.json")

if __name__ == "__main__":
    if os.path.exists(COOKIE_FILE) and input("使用已保存的 cookie？(y/n): ").lower() == 'y':
        print(f"✅ 使用已保存的 cookie：{COOKIE_FILE}")
        exit(0)
    
    print("="*60)
    print("步骤 1: 手动登录 TradingView")
    print("="*60)
    
    options = webdriver.ChromeOptions()
    options.add_experimental_option("detach", True)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    driver.get(LOGIN_URL)
    
    print(f"✅ 已打开登录页面：{LOGIN_URL}")
    print("👉 请手动登录，完成后按回车...")
    input()
    
    cookies = driver.get_cookies()
    print(f"✅ 获取到 {len(cookies)} 个 cookie")
    
    with open(COOKIE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)
    
    driver.quit()
    print(f"✅ Cookie 已保存：{COOKIE_FILE}\n")
