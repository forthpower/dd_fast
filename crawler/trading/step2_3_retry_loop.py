import os
import time
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from selenium import webdriver

from crawler.trading import step2_screenshot, step3_recognize

BASE_DIR = os.path.dirname(__file__)
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "result", "screenshots")
CSV_DIR = os.path.join(BASE_DIR, "result", "csv")


class TradingViewRetryLoop:
    def __init__(self):
        self.url_to_number: Dict[str, str] = {}
        self.sleep_time = 20

    def _load_existing_numbers(self) -> Dict[str, str]:
        if not os.path.exists(CSV_DIR):
            return {}
        files = [f for f in os.listdir(CSV_DIR) if 'last_number' in f and f.endswith(".csv")]
        if not files:
            return {}
        latest = max(files, key=lambda f: os.path.getmtime(os.path.join(CSV_DIR, f)))
        url_to_number = {}
        with open(os.path.join(CSV_DIR, latest), "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 2 and row[0].strip() and row[1].strip() and float(row[1].strip()) < 100:
                    url_to_number[row[0].strip()] = row[1].strip()
        print(f"📄 预加载: {len(url_to_number)} 条")
        return url_to_number

    def _screenshot(self, urls: List[str]) -> Dict[str, str]:
        if not urls:
            return {}
        session = step2_screenshot.load_cookie()
        options = webdriver.ChromeOptions()
        options.add_experimental_option("detach", True)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
        driver = webdriver.Chrome(options=options)
        driver.maximize_window()
        driver.execute_cdp_cmd("Network.enable", {})
        step2_screenshot.inject_cookies(driver, session)
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        url_to_image: Dict[str, str] = {}
        for idx, url in enumerate(urls, 1):
            print(f"[{idx}/{len(urls)}] {url}")
            driver.get(url)
            time.sleep(self.sleep_time)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            url_part = url.split("/")[-2] if "/" in url else "tradingview"
            screenshot_name = f"tradingview_{url_part}_{timestamp}.png"
            screenshot_path = os.path.join(SCREENSHOTS_DIR, screenshot_name)
            try:
                driver.save_screenshot(screenshot_path)
                url_to_image[url] = screenshot_path
            except Exception as e:
                print(f"❌ 失败: {e}")
        driver.quit()
        return url_to_image

    def _recognize_number(self, image_path: str) -> str | None:
        text = step3_recognize.recognize_image(image_path)
        if not text:
            return None
        num = step3_recognize.extract_nov_last_number(text)
        if not num:
            return None
        num_str = str(num).strip()
        return num_str if num_str and num_str != "0" else None

    def _clean_old_images(self):
        folder = SCREENSHOTS_DIR
        if not os.path.exists(folder):
            return
        files = [
            os.path.join(folder, f)
            for f in os.listdir(folder)
            if os.path.isfile(os.path.join(folder, f))
               and Path(f).suffix.lower() in {".png", ".jpg", ".jpeg"}
        ]
        if len(files) <= 1:
            return
        groups: Dict[str, List[str]] = {}
        for p in files:
            name = Path(p).stem
            key = "_".join(name.split("_")[:-1]) if "_" in name else name
            groups.setdefault(key, []).append(p)
        for paths in groups.values():
            if len(paths) > 1:
                paths.sort(key=os.path.getmtime)
                for old in paths[:-1]:
                    try:
                        os.remove(old)
                    except OSError:
                        pass

    def run(self):
        urls = step2_screenshot.load_urls()
        if not urls:
            print("❌ 没有 URL")
            return
        self.url_to_number = self._load_existing_numbers()
        remaining: Set[str] = {u for u in urls if u not in self.url_to_number}
        print(f"需要处理 {len(remaining)} 条")
        iteration = 0
        while remaining:
            iteration += 1
            print(f"\n第 {iteration} 轮，剩余 {len(remaining)} 个")
            batch = sorted(remaining)
            url_to_image = self._screenshot(batch)
            self._clean_old_images()
            if not url_to_image:
                break
            failed: Dict[str, str] = {}
            for url, screenshot_path in url_to_image.items():
                num = self._recognize_number(screenshot_path)
                if num:
                    self.url_to_number[url] = num
                    remaining.discard(url)
                    print(f"✅ {url} -> {num}")
                else:
                    failed[url] = screenshot_path
            if len(self.url_to_number) == len(urls) or iteration > 2:
                break
            self.sleep_time += 20
        os.makedirs(CSV_DIR, exist_ok=True)
        out_path = os.path.join(CSV_DIR, f"nov_last_number{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
        with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "Nov列最后一个数字"])
            for url in urls:
                writer.writerow([url, self.url_to_number.get(url, "")])
        print(f"\n✅ 完成 {len(self.url_to_number)}/{len(urls)} 个")
        print(f"📄 {out_path}")


if __name__ == "__main__":
    TradingViewRetryLoop().run()
