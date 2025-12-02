import os
import base64
import re
from openai import OpenAI

QWEN_API_KEY = "sk-1a258df43a714d8eaf0f79dbfaa47308"
QWEN_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"

client = OpenAI(api_key=QWEN_API_KEY, base_url=QWEN_BASE_URL)
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
        completion = client.chat.completions.create(
            model="qwen-vl-plus",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}},
                    {"type": "text", "text": prompt or PROMPT},
                ],
            }],
            temperature=0.1,
            max_tokens=2000,
        )
        if completion.choices:
            return completion.choices[0].message.content.strip()
    except Exception:
        return None
    return None


def recognize_image_with_prompt(path: str, custom_prompt: str) -> str | None:
    return recognize_image(path, prompt=custom_prompt)


def parse_csv(text: str):
    lines = []
    for line in text.split("\n"):
        line = line.strip()
        if line and ("," in line or "\t" in line):
            row = [c.strip() for c in (line.split(",") if "," in line else line.split("\t"))]
            if any(row):
                lines.append(row)
    return lines if lines else [[text]]


def extract_nov_last_number(text: str) -> str | None:
    """从识别结果中提取 Nov 列的最后一个数字"""
    text = text.strip()
    # 如果直接返回了数字
    if text and text.replace(".", "").replace("-", "").isdigit():
        return text
    # 尝试从 CSV 格式中提取
    lines = parse_csv(text)
    if not lines:
        return None
    # 查找 Nov 列的索引
    header_row = None
    nov_col_idx = None
    for i, row in enumerate(lines):
        for j, cell in enumerate(row):
            if "nov" in str(cell).lower():
                nov_col_idx = j
                header_row = i
                break
        if nov_col_idx is not None:
            break
    if nov_col_idx is None:
        return None
    # 从 Nov 列提取最后一个非空数字
    for row in reversed(lines[header_row + 1:]):
        if nov_col_idx < len(row):
            val = str(row[nov_col_idx]).strip()
            if val and val.replace(".", "").replace("-", "").isdigit():
                return val
    return None
