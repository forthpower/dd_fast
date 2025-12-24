import base64
import requests
import csv
from pathlib import Path
from datetime import datetime

GEMINI_API_KEY = "AIzaSyC9qr72bGb3kGGzG88Yo4UjT5nUUtWpckU"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-preview:generateContent"
PROMPT = (
    "请识别图片右下角的月份表格（包含 Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec 等月份列），"
    "并严格遵守以下规则："
    "1）找到 Nov（十一月）这一列；"
    "2）提取 Nov 列中的最后一个数据（最下方的数字）；"
    "3）只输出这个数字，不要输出任何其他内容；"
    "4）如果找不到表格或 Nov 列，输出：无数据。"
)


def recognize_image(path: str, prompt: str | None = None) -> str | None:
    try:
        with open(path, "rb") as f:
            image_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        mime_type = "image/png" if path.lower().endswith(".png") else "image/jpeg"
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt or PROMPT},
                    {"inline_data": {"mime_type": mime_type, "data": image_base64}}
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 500,
            }
        }
        
        response = requests.post(
            f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if "candidates" in result and result["candidates"]:
                content = result["candidates"][0].get("content", {})
                parts = content.get("parts", [])
                if parts and "text" in parts[0]:
                    return parts[0]["text"].strip()
    except Exception:
        pass
    return None


def main():
    import sys
    
    script_dir = Path(__file__).parent
    result_dir = script_dir / "result" / "screenshots"
    
    if len(sys.argv) > 1:
        input_path = Path(sys.argv[1])
        image_files = [input_path] if input_path.is_file() else list(input_path.glob("*.png")) if input_path.is_dir() else []
    else:
        image_files = list(result_dir.glob("*.png")) if result_dir.exists() else []
    
    if not image_files:
        print("错误: 未找到图片文件")
        return
    
    print(f"找到 {len(image_files)} 个图片，开始识别...")
    
    results = []
    for i, img_path in enumerate(image_files, 1):
        print(f"[{i}/{len(image_files)}] {img_path.name}")
        result = recognize_image(str(img_path))
        results.append([img_path.name, result or "识别失败"])
    
    # 保存到 CSV
    csv_path = script_dir / f"recognition_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["图片文件名", "识别结果"])
        writer.writerows(results)
    
    print(f"\n完成! 结果已保存到: {csv_path}")
    print(f"成功: {sum(1 for r in results if r[1] != '识别失败')} 个")

if __name__ == "__main__":
    main()